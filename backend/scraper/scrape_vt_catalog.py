#!/usr/bin/env python3
"""
VT Course Catalog Scraper - Using Playwright
Scrapes all courses from catalog.vt.edu
"""

import asyncio
import json
import re
import os
from playwright.async_api import async_playwright

# CONFIG
OUTPUT_DIR = "data"
OUTPUT_FILE = f"{OUTPUT_DIR}/courses_scraped.json"
FINAL_OUTPUT = f"{OUTPUT_DIR}/courses.json"
INDEX_URL = "https://catalog.vt.edu/undergraduate/course-descriptions/"
BASE_URL = "https://catalog.vt.edu"

# Subjects we care about most for CS degree
PRIORITY_SUBJECTS = [
    'cs', 'math', 'stat', 'phys', 'chem', 'biol',
    'engl', 'comm', 'phil', 'econ', 'psyc', 'soc',
    'hist', 'pols', 'enge', 'ece', 'geog', 'art', 'mus'
]

def parse_credits(text):
    """Extract credits from text like '(3H,3C)' or '3 credits' or '3 Credit Hours'"""
    # Try (XH,XC) format first
    match = re.search(r'\((\d+)H,\s*(\d+)C\)', text)
    if match:
        return int(match.group(2))  # Return credit hours (C)

    # Try "X credits" format
    match = re.search(r'(\d+)\s*(?:credit|Credit)', text)
    if match:
        return int(match.group(1))

    # Try just a number at the end
    match = re.search(r'(\d+)\s*$', text)
    if match:
        return int(match.group(1))

    return 3  # Default


def parse_prerequisites(text):
    """Extract prerequisite course codes from text"""
    if not text or text.lower() == 'none':
        return []

    # Find all course codes like "CS 2114" or "MATH 1226"
    codes = re.findall(r'([A-Z]{2,4})\s*(\d{4})', text.upper())
    prereqs = [f"{dept} {num}" for dept, num in codes]

    # Remove duplicates while preserving order
    seen = set()
    unique_prereqs = []
    for p in prereqs:
        if p not in seen:
            seen.add(p)
            unique_prereqs.append(p)

    return unique_prereqs


def determine_category(subject, course_num, course_name):
    """Determine course category based on subject and number"""
    num = int(course_num) if course_num.isdigit() else 0
    name_lower = course_name.lower()

    if subject == 'CS':
        if num in [1114]:
            return 'cs_core'
        if num in [2114, 2505, 2506, 3114, 3214]:
            return 'cs_core'
        if num == 4104:
            return 'cs_theory'
        if num in [4114, 4254, 4284]:
            return 'cs_systems'
        if num in [4704, 4784, 4884, 4274, 4664, 4094]:
            return 'capstone'
        if num < 2000:
            return 'cs_intro'
        if num >= 3000:
            return 'cs_elective'
        return 'cs_intro'

    if subject == 'MATH':
        if num in [1225, 1226, 2114]:
            return 'math_core'
        if num in [2534, 3034]:
            return 'math_discrete'
        return 'math_elective'

    if subject == 'STAT':
        if num in [4705, 4714, 3005, 3104]:
            return 'stats'
        return 'stats_elective'

    if subject in ['PHYS', 'CHEM', 'BIOL']:
        return 'science'

    if subject in ['ENGL', 'COMM', 'PHIL', 'ECON', 'PSYC', 'SOC', 'HIST', 'POLS', 'GEOG', 'ART', 'MUS']:
        return 'pathways'

    if subject in ['ENGE', 'ECE']:
        return 'engineering'

    return 'elective'


async def scrape_catalog():
    """Main scraping function"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set to False to see browser
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        print(f"🕷️  Crawling Index: {INDEX_URL}")
        await page.goto(INDEX_URL, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(3000)

        # Get all subject links
        subject_links = await page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a[href*="/undergraduate/course-descriptions/"]'));
            return anchors
                .map(a => ({
                    href: a.getAttribute('href'),
                    text: a.innerText.trim()
                }))
                .filter(item => item.href && item.href.split('/').filter(x => x).length === 3);
        }""")

        # Deduplicate and sort
        seen_urls = set()
        unique_links = []
        for link in subject_links:
            if link['href'] not in seen_urls and link['href'] != '/undergraduate/course-descriptions/':
                seen_urls.add(link['href'])
                unique_links.append(link)

        print(f"✅ Found {len(unique_links)} subjects")

        # Sort to prioritize important subjects
        def sort_key(link):
            subject = link['href'].strip('/').split('/')[-1].lower()
            if subject in PRIORITY_SUBJECTS:
                return (0, PRIORITY_SUBJECTS.index(subject))
            return (1, subject)

        unique_links.sort(key=sort_key)

        all_courses = {}
        failed_subjects = []

        for i, link in enumerate(unique_links):
            relative_url = link['href']
            full_url = BASE_URL + relative_url
            subject_code = relative_url.strip('/').split('/')[-1].upper()

            print(f"\n[{i+1}/{len(unique_links)}] Processing {subject_code}...")

            try:
                await page.goto(full_url, wait_until='domcontentloaded', timeout=45000)
                await page.wait_for_timeout(2000)  # Wait for JS rendering

                # Wait for course blocks to load
                try:
                    await page.wait_for_selector('.courseblock, .sc_sccoursedescs', timeout=5000)
                except:
                    print(f"   ⚠️  No courses found for {subject_code}")
                    continue

                # Extract course data
                courses_on_page = await page.evaluate("""() => {
                    const results = [];

                    // Get course blocks
                    const blocks = document.querySelectorAll('.courseblock');

                    blocks.forEach(block => {
                        // Extract course code
                        const codeEl = block.querySelector('.detail-code strong, .detail-code');
                        // Extract course title
                        const titleEl = block.querySelector('.detail-title strong, .detail-title');
                        // Extract credits
                        const creditsEl = block.querySelector('.detail-hours_html strong, .detail-hours_html');
                        // Extract description and extra info
                        const extraEls = block.querySelectorAll('.courseblockextra');

                        const code = codeEl ? codeEl.innerText.trim() : '';
                        let title = titleEl ? titleEl.innerText.trim() : '';
                        const credits = creditsEl ? creditsEl.innerText.trim() : '';
                        const extraInfo = Array.from(extraEls).map(e => e.innerText.trim()).join(' | ');

                        // Clean up title (remove leading dash)
                        title = title.replace(/^[-–]\\s*/, '').trim();

                        if (code) {
                            results.push({
                                code: code,
                                title: title,
                                credits_text: credits,
                                extra_info: extraInfo,
                                full_text: block.innerText
                            });
                        }
                    });

                    return results;
                }""")

                added_count = 0
                for course_data in courses_on_page:
                    code_raw = course_data.get('code', '')
                    title = course_data.get('title', '')
                    credits_text = course_data.get('credits_text', '')
                    full_text = course_data.get('full_text', '')
                    extra_info = course_data.get('extra_info', '')

                    # Parse course code
                    code_match = re.search(r'([A-Z]{2,4})\s*(\d{4})', code_raw)
                    if not code_match:
                        continue

                    course_id = f"{code_match.group(1)} {code_match.group(2)}"

                    # Use the title directly (already cleaned)
                    name = title if title else "Course"

                    # Extract credits from credits text like "(3 credits)" or "(3H,3C)"
                    credits = parse_credits(credits_text)

                    # Extract prerequisites from extra_info
                    prereq_text = ""
                    prereq_match = re.search(
                        r'(?:Pre(?:requisite)?s?|Pre:)\s*[:\-]?\s*(.+?)(?:Co(?:requisite)?|Cross|$|\n)',
                        extra_info,
                        re.IGNORECASE
                    )
                    if prereq_match:
                        prereq_text = prereq_match.group(1)

                    prereqs = parse_prerequisites(prereq_text)

                    # Determine category
                    parts = course_id.split()
                    subject = parts[0] if parts else subject_code
                    course_num = parts[1] if len(parts) > 1 else '0'
                    category = determine_category(subject, course_num, name)

                    # Store course
                    all_courses[course_id] = {
                        "name": name[:100],  # Truncate long names
                        "credits": credits,
                        "prereqs": prereqs,
                        "category": category,
                        "description": course_data['description'][:500] if course_data['description'] else ""
                    }
                    added_count += 1

                print(f"   ✅ Added {added_count} courses")

                # Save progress every 10 subjects
                if (i + 1) % 10 == 0:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(all_courses, f, indent=2)
                    print(f"   💾 Progress saved ({len(all_courses)} courses total)")

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                failed_subjects.append(subject_code)

            # Small delay to be nice to the server
            await asyncio.sleep(0.5)

        # Final save
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_courses, f, indent=2)

        # Also save in the format the app expects
        with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(all_courses, f, indent=2)

        await browser.close()

        print(f"\n{'='*50}")
        print(f"🎉 DONE! Scraped {len(all_courses)} courses")
        print(f"📁 Saved to: {FINAL_OUTPUT}")
        if failed_subjects:
            print(f"⚠️  Failed subjects: {', '.join(failed_subjects)}")

        # Print summary by category
        categories = {}
        for code, data in all_courses.items():
            cat = data.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n📊 Courses by category:")
        for cat, count in sorted(categories.items()):
            print(f"   {cat}: {count}")


async def scrape_single_subject(subject_code):
    """Scrape just one subject for testing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = f"{BASE_URL}/undergraduate/course-descriptions/{subject_code.lower()}/"
        print(f"Testing: {url}")

        await page.goto(url, wait_until='domcontentloaded', timeout=60000)
        await page.wait_for_timeout(5000)  # Wait for JS to load

        # Print page structure for debugging
        structure = await page.evaluate("""() => {
            const blocks = document.querySelectorAll('.courseblock');
            if (blocks.length > 0) {
                const first = blocks[0];
                return {
                    count: blocks.length,
                    firstBlock: first.innerHTML.substring(0, 1000),
                    classes: first.className
                };
            }
            return { count: 0, html: document.body.innerHTML.substring(0, 2000) };
        }""")

        print(f"Found {structure.get('count', 0)} course blocks")
        print(f"Sample HTML:\n{structure.get('firstBlock', structure.get('html', 'N/A'))[:500]}")

        await browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test mode: scrape single subject
        subject = sys.argv[2] if len(sys.argv) > 2 else 'cs'
        asyncio.run(scrape_single_subject(subject))
    else:
        # Full scrape
        asyncio.run(scrape_catalog())
