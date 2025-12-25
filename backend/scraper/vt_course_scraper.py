"""
VT Course Catalog Scraper
=========================
Scrapes Virginia Tech's course catalog which is a single-page application.
Uses Playwright for browser automation to handle the dynamic content.

Usage:
    python vt_course_scraper.py --subject CS
    python vt_course_scraper.py --subject CS --output courses.json
    python vt_course_scraper.py --all-cs-related
"""

import asyncio
import json
import re
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

# Try to import playwright, install if not available
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Installing playwright...")
    import subprocess
    subprocess.run(["pip", "install", "playwright"])
    subprocess.run(["playwright", "install", "chromium"])
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


VT_CATALOG_URL = "https://catalog.vt.edu/course-search/"
OUTPUT_DIR = Path(__file__).parent.parent / "data"


async def scrape_vt_courses(
    subjects: list[str] = None,
    headless: bool = True,
    output_file: str = None
) -> dict:
    """
    Scrape courses from VT's course catalog.

    Args:
        subjects: List of subject codes to scrape (e.g., ['CS', 'MATH', 'STAT'])
        headless: Run browser in headless mode
        output_file: Path to save results

    Returns:
        Dictionary of courses keyed by course code
    """

    if subjects is None:
        subjects = ['CS']

    all_courses = {}

    async with async_playwright() as p:
        print(f"Launching browser (headless={headless})...")
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        for subject in subjects:
            print(f"\n{'='*50}")
            print(f"Scraping {subject} courses...")
            print('='*50)

            try:
                # Navigate to course search
                await page.goto(VT_CATALOG_URL, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # Find and fill the subject search box
                # VT's catalog has a subject filter dropdown
                subject_input = page.locator('input[placeholder*="Subject"]').first
                if await subject_input.count() == 0:
                    subject_input = page.locator('#crit-subject').first
                if await subject_input.count() == 0:
                    subject_input = page.locator('[aria-label*="Subject"]').first

                if await subject_input.count() > 0:
                    await subject_input.click()
                    await subject_input.fill(subject)
                    await asyncio.sleep(1)

                    # Click the search/filter button or press Enter
                    await page.keyboard.press('Enter')
                    await asyncio.sleep(2)
                else:
                    print(f"Could not find subject input field")
                    # Try alternative: look for a select dropdown
                    select = page.locator('select[name*="subject"]').first
                    if await select.count() > 0:
                        await select.select_option(value=subject)
                        await asyncio.sleep(2)

                # Wait for results to load
                await page.wait_for_load_state('networkidle', timeout=15000)
                await asyncio.sleep(2)

                # Try to find course results - VT uses various selectors
                course_selectors = [
                    '.course-result',
                    '.course',
                    '[class*="course"]',
                    '.search-result',
                    'div[data-course]',
                    '.result-item'
                ]

                courses_found = False
                for selector in course_selectors:
                    elements = page.locator(selector)
                    count = await elements.count()
                    if count > 0:
                        print(f"Found {count} courses using selector: {selector}")
                        courses_found = True

                        for i in range(count):
                            try:
                                element = elements.nth(i)
                                course_data = await extract_course_data(element, subject)
                                if course_data and course_data.get('code'):
                                    all_courses[course_data['code']] = course_data
                                    print(f"  ✓ {course_data['code']}: {course_data.get('name', 'Unknown')}")
                            except Exception as e:
                                print(f"  ✗ Error extracting course {i}: {e}")

                        break

                if not courses_found:
                    # Alternative: try to scrape from page text
                    print("Trying text-based extraction...")
                    page_text = await page.content()
                    courses = extract_courses_from_html(page_text, subject)
                    for course in courses:
                        if course.get('code'):
                            all_courses[course['code']] = course
                            print(f"  ✓ {course['code']}: {course.get('name', 'Unknown')}")

            except PlaywrightTimeout:
                print(f"Timeout while scraping {subject}")
            except Exception as e:
                print(f"Error scraping {subject}: {e}")

        await browser.close()

    # Save results
    if output_file:
        output_path = Path(output_file)
    else:
        output_path = OUTPUT_DIR / "scraped_courses.json"

    output_path.parent.mkdir(exist_ok=True)

    result = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "subjects": subjects,
            "total_courses": len(all_courses)
        },
        "courses": all_courses
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Scraped {len(all_courses)} courses total")
    print(f"Saved to: {output_path}")

    return all_courses


async def extract_course_data(element, subject: str) -> Optional[dict]:
    """Extract course data from a course element."""
    try:
        text = await element.inner_text()
        html = await element.inner_html()

        # Parse course code (e.g., "CS 1114" or "CS1114")
        code_match = re.search(rf'{subject}\s*(\d{{4}})', text, re.IGNORECASE)
        if not code_match:
            return None

        course_code = f"{subject} {code_match.group(1)}"

        # Parse course name - usually after the code
        name_match = re.search(rf'{subject}\s*\d{{4}}\s*[-–:.]?\s*(.+?)(?:\d+\s*(?:cr|credit)|$)', text, re.IGNORECASE)
        course_name = name_match.group(1).strip() if name_match else ""
        course_name = re.sub(r'\s+', ' ', course_name).strip()

        # Parse credits
        credits_match = re.search(r'(\d+)\s*(?:cr|credit|hr|hour)', text, re.IGNORECASE)
        credits = int(credits_match.group(1)) if credits_match else 3

        # Parse prerequisites from text
        prereqs = []
        prereq_match = re.search(r'prereq(?:uisite)?s?[:\s]+([^.]+)', text, re.IGNORECASE)
        if prereq_match:
            prereq_text = prereq_match.group(1)
            # Find all course codes in prereq text
            prereq_codes = re.findall(r'([A-Z]{2,4})\s*(\d{4})', prereq_text)
            prereqs = [f"{dept} {num}" for dept, num in prereq_codes]

        # Parse corequisites
        coreqs = []
        coreq_match = re.search(r'coreq(?:uisite)?s?[:\s]+([^.]+)', text, re.IGNORECASE)
        if coreq_match:
            coreq_text = coreq_match.group(1)
            coreq_codes = re.findall(r'([A-Z]{2,4})\s*(\d{4})', coreq_text)
            coreqs = [f"{dept} {num}" for dept, num in coreq_codes]

        # Determine category based on course number
        course_num = int(code_match.group(1))
        if subject == 'CS':
            if course_num < 3000:
                category = 'cs_core' if course_num in [1114, 2104, 2114, 2505, 2506] else 'cs_core'
            elif course_num < 4000:
                category = 'cs_core' if course_num in [3114, 3214, 3304] else 'cs_elective'
            else:
                category = 'cs_core' if course_num == 4104 else 'cs_elective'
        elif subject == 'MATH':
            category = 'math'
        elif subject == 'STAT':
            category = 'math'
        elif subject == 'PHYS':
            category = 'science'
        elif subject == 'CHEM':
            category = 'science'
        elif subject == 'BIOL':
            category = 'science'
        else:
            category = 'elective'

        return {
            "code": course_code,
            "name": course_name[:100] if course_name else f"{subject} {course_num}",
            "credits": credits,
            "prereqs": prereqs,
            "coreqs": coreqs,
            "category": category,
            "difficulty": 3,  # Default
            "workload": 3,    # Default
            "tags": [],
            "professors": [],
            "description": "",
            "typically_offered": []
        }

    except Exception as e:
        print(f"Error in extract_course_data: {e}")
        return None


def extract_courses_from_html(html: str, subject: str) -> list[dict]:
    """Extract courses from raw HTML using regex patterns."""
    courses = []

    # Pattern to match course entries
    # VT format: "CS 1114 - Introduction to Software Design (3 credits)"
    pattern = rf'{subject}\s*(\d{{4}})\s*[-–:]?\s*([^(<]+?)(?:\((\d+)\s*(?:cr|credit|hr))'

    matches = re.findall(pattern, html, re.IGNORECASE)

    for match in matches:
        course_num, name, credits = match
        code = f"{subject} {course_num}"

        if code not in [c.get('code') for c in courses]:
            courses.append({
                "code": code,
                "name": name.strip()[:100],
                "credits": int(credits) if credits else 3,
                "prereqs": [],
                "coreqs": [],
                "category": determine_category(subject, int(course_num)),
                "difficulty": 3,
                "workload": 3,
                "tags": [],
                "professors": [],
                "description": "",
                "typically_offered": []
            })

    return courses


def determine_category(subject: str, course_num: int) -> str:
    """Determine course category based on subject and number."""
    if subject == 'CS':
        core_courses = {1114, 2104, 2114, 2505, 2506, 3114, 3214, 3304, 4104}
        return 'cs_core' if course_num in core_courses else 'cs_elective'
    elif subject in ['MATH', 'STAT']:
        return 'math'
    elif subject in ['PHYS', 'CHEM', 'BIOL']:
        return 'science'
    elif subject in ['ENGL', 'COMM', 'PHIL', 'MUSI', 'PSYC', 'ECON', 'HIST']:
        return 'pathway'
    return 'elective'


async def scrape_checksheet(url: str = None) -> dict:
    """
    Scrape a VT degree checksheet PDF or webpage for requirements.
    """
    if url is None:
        url = "https://cs.vt.edu/Undergraduate/DegreeRequirements.html"

    # This would need PDF parsing or HTML scraping depending on the format
    # For now, return the known CS requirements
    return {
        "cs_major": {
            "core_required": [
                "CS 1114", "CS 2104", "CS 2114", "CS 2505", "CS 2506",
                "CS 3114", "CS 3214", "CS 3304", "CS 4104"
            ],
            "math_required": [
                "MATH 1225", "MATH 1226", "MATH 2114", "MATH 3134", "STAT 3006"
            ],
            "science_required": [
                "PHYS 2305"
            ],
            "electives_needed": 3
        }
    }


def merge_with_existing(scraped: dict, existing_path: Path) -> dict:
    """Merge scraped courses with existing course data."""
    if existing_path.exists():
        with open(existing_path, 'r') as f:
            existing = json.load(f)

        existing_courses = existing.get('courses', {})

        # Merge - scraped data takes precedence for new fields, keep existing enriched data
        for code, data in scraped.items():
            if code in existing_courses:
                # Keep existing enriched data (professors, difficulty, etc.)
                for key in ['professors', 'difficulty', 'workload', 'tags', 'description']:
                    if existing_courses[code].get(key):
                        data[key] = existing_courses[code][key]
            existing_courses[code] = data

        existing['courses'] = existing_courses
        existing['metadata']['last_updated'] = datetime.now().isoformat()
        return existing

    return {
        "metadata": {"last_updated": datetime.now().isoformat()},
        "courses": scraped
    }


async def main():
    parser = argparse.ArgumentParser(description='Scrape VT Course Catalog')
    parser.add_argument('--subject', '-s', type=str, help='Subject code (e.g., CS, MATH)')
    parser.add_argument('--all-cs-related', action='store_true', help='Scrape all CS-related subjects')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--merge', action='store_true', help='Merge with existing courses.json')

    args = parser.parse_args()

    if args.all_cs_related:
        subjects = ['CS', 'MATH', 'STAT', 'PHYS', 'ECE', 'ENGL', 'COMM']
    elif args.subject:
        subjects = [args.subject.upper()]
    else:
        subjects = ['CS']

    courses = await scrape_vt_courses(
        subjects=subjects,
        headless=not args.visible,
        output_file=args.output
    )

    if args.merge:
        existing_path = OUTPUT_DIR / "courses.json"
        merged = merge_with_existing(courses, existing_path)
        with open(existing_path, 'w') as f:
            json.dump(merged, f, indent=2)
        print(f"Merged with {existing_path}")

    return courses


if __name__ == '__main__':
    asyncio.run(main())
