#!/usr/bin/env python3
"""
VT Course Catalog Scraper - Complete Edition
Scrapes ALL courses from catalog.vt.edu with proper names and prerequisites
"""

import asyncio
import json
import re
import os
from playwright.async_api import async_playwright

# CONFIG
OUTPUT_DIR = "data"
OUTPUT_FILE = f"{OUTPUT_DIR}/courses.json"
INDEX_URL = "https://catalog.vt.edu/undergraduate/course-descriptions/"
BASE_URL = "https://catalog.vt.edu"


def parse_credits(text):
    """Extract credits from text like '(3 credits)' or '(3H,3C)'"""
    if not text:
        return 3

    # Try "(X credits)" format
    match = re.search(r'\((\d+)\s*credits?\)', text, re.I)
    if match:
        return int(match.group(1))

    # Try (XH,XC) format
    match = re.search(r'\((\d+)H,\s*(\d+)C\)', text)
    if match:
        return int(match.group(2))

    # Try just a number
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))

    return 3


def parse_prerequisites(text):
    """Extract prerequisite course codes from text"""
    if not text:
        return []

    # Find all course codes like "CS 2114" or "MATH 1226"
    codes = re.findall(r'([A-Z]{2,4})\s*(\d{4})', text.upper())
    prereqs = [f"{dept} {num}" for dept, num in codes]

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for p in prereqs:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return unique


def determine_category(subject, course_num, course_name=""):
    """Determine course category based on subject and number"""
    try:
        num = int(course_num)
    except:
        num = 0

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

    if subject in ['ENGL', 'COMM', 'PHIL', 'ECON', 'PSYC', 'SOC', 'HIST', 'POLS', 'GEOG', 'ART', 'MUS',
                   'SPAN', 'FREN', 'GER', 'CHN', 'JPN', 'RUS', 'ARBC', 'LAT', 'GR', 'PORT', 'ITAL',
                   'HUM', 'REL', 'RLCL', 'WGS', 'AFST', 'DANC', 'TA', 'CINE', 'MUS']:
        return 'pathways'

    if subject in ['ENGE', 'ECE', 'ME', 'CEE', 'AOE', 'MSE', 'CHE', 'ISE', 'BSE', 'MINE', 'ESM']:
        return 'engineering'

    return 'elective'


async def scrape_all_courses():
    """Main scraping function - get ALL courses with proper data"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    all_courses = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        print(f"Fetching subject index: {INDEX_URL}")
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
                .filter(item => {
                    if (!item.href) return false;
                    const parts = item.href.split('/').filter(x => x);
                    // Must be exactly: undergraduate/course-descriptions/SUBJECT
                    return parts.length === 3 &&
                           parts[0] === 'undergraduate' &&
                           parts[1] === 'course-descriptions' &&
                           !item.href.includes('.pdf');
                });
        }""")

        # Deduplicate
        seen_urls = set()
        unique_links = []
        for link in subject_links:
            if link['href'] not in seen_urls:
                seen_urls.add(link['href'])
                unique_links.append(link)

        print(f"Found {len(unique_links)} subjects to scrape")

        for i, link in enumerate(unique_links):
            relative_url = link['href']
            full_url = BASE_URL + relative_url
            subject_code = relative_url.strip('/').split('/')[-1].upper()

            print(f"[{i+1}/{len(unique_links)}] {subject_code}...", end=" ", flush=True)

            try:
                await page.goto(full_url, wait_until='domcontentloaded', timeout=45000)
                await page.wait_for_timeout(2000)

                # Wait for course blocks
                try:
                    await page.wait_for_selector('.courseblock', timeout=8000)
                except:
                    print("no courses")
                    continue

                # Extract course data using the correct selectors
                courses_data = await page.evaluate("""() => {
                    const results = [];
                    const blocks = document.querySelectorAll('.courseblock');

                    blocks.forEach(block => {
                        // Get course code from .detail-code strong
                        const codeEl = block.querySelector('.detail-code strong');
                        if (!codeEl) return;
                        const code = codeEl.innerText.trim();

                        // Get course name from .detail-title strong
                        const titleEl = block.querySelector('.detail-title strong');
                        let name = titleEl ? titleEl.innerText.trim() : '';
                        // Remove leading dash
                        name = name.replace(/^[-–]\\s*/, '').trim();

                        // Get credits from .detail-hours_html strong
                        const creditsEl = block.querySelector('.detail-hours_html strong');
                        const creditsText = creditsEl ? creditsEl.innerText.trim() : '';

                        // Get full text for description and prerequisites
                        const fullText = block.innerText;

                        // Extract description (usually the first .courseblockextra)
                        const descEl = block.querySelector('.courseblockextra');
                        let description = descEl ? descEl.innerText.trim() : '';
                        // Stop at "Prerequisite" or other fields
                        const descEnd = description.search(/Prerequisite|Pre:|Co-requisite|Corequisite|Pathway|Instructional|Cross-listed/i);
                        if (descEnd > 0) {
                            description = description.substring(0, descEnd).trim();
                        }

                        // Extract prerequisites
                        const prereqMatch = fullText.match(/Prerequisite\\(?s?\\)?:\\s*([^\\n]+)/i);
                        const prereqText = prereqMatch ? prereqMatch[1] : '';

                        // Extract corequisites
                        const coreqMatch = fullText.match(/Co-?requisite\\(?s?\\)?:\\s*([^\\n]+)/i);
                        const coreqText = coreqMatch ? coreqMatch[1] : '';

                        if (code) {
                            results.push({
                                code: code,
                                name: name || code,
                                credits_text: creditsText,
                                description: description,
                                prereq_text: prereqText,
                                coreq_text: coreqText
                            });
                        }
                    });

                    return results;
                }""")

                added = 0
                for course in courses_data:
                    code = course['code']

                    # Parse code into subject and number
                    code_match = re.match(r'([A-Z]{2,4})\s*(\d{4})', code)
                    if not code_match:
                        continue

                    subject = code_match.group(1)
                    course_num = code_match.group(2)
                    normalized_code = f"{subject} {course_num}"

                    # Parse prerequisites and corequisites
                    prereqs = parse_prerequisites(course['prereq_text'])
                    coreqs = parse_prerequisites(course['coreq_text'])

                    # Don't include self as prereq
                    prereqs = [p for p in prereqs if p != normalized_code]
                    coreqs = [c for c in coreqs if c != normalized_code]

                    # Parse credits
                    credits = parse_credits(course['credits_text'])

                    all_courses[normalized_code] = {
                        "name": course['name'] if course['name'] and course['name'] != code else f"{subject} Course",
                        "credits": credits,
                        "prereqs": prereqs,
                        "coreqs": coreqs,
                        "category": determine_category(subject, course_num, course['name']),
                        "description": course['description'][:500] if course['description'] else ""
                    }
                    added += 1

                print(f"{added} courses")

                # Save progress every 20 subjects
                if (i + 1) % 20 == 0:
                    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(all_courses, f, indent=2)
                    print(f"   [Progress saved: {len(all_courses)} courses]")

            except Exception as e:
                print(f"error: {str(e)[:60]}")

            await asyncio.sleep(0.3)

        await browser.close()

    # Final save
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_courses, f, indent=2)

    print(f"\n{'='*60}")
    print(f"DONE! Scraped {len(all_courses)} courses")
    print(f"Saved to: {OUTPUT_FILE}")

    # Summary by category
    categories = {}
    for code, data in all_courses.items():
        cat = data.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nBy category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    # Show sample CS courses with prereqs
    print(f"\nSample CS courses with prerequisites:")
    cs_courses = [(k, v) for k, v in all_courses.items() if k.startswith('CS ')]
    for code, data in sorted(cs_courses)[:15]:
        prereqs = data.get('prereqs', [])
        print(f"  {code}: {data['name'][:40]} -> prereqs: {prereqs}")


if __name__ == "__main__":
    asyncio.run(scrape_all_courses())
