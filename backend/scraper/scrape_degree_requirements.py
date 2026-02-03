#!/usr/bin/env python3
"""
VT Degree Requirements Scraper
================================
Scrapes degree checksheet pages from catalog.vt.edu for all undergraduate programs.
Uses Playwright for JavaScript-rendered pages and Gemini AI for parsing complex HTML.

Usage:
    python scrape_degree_requirements.py              # Scrape all programs
    python scrape_degree_requirements.py --major CS   # Scrape specific major
    python scrape_degree_requirements.py --test       # Test with 5 known majors
"""

import asyncio
import json
import re
import os
import sys
import argparse
from pathlib import Path
from playwright.async_api import async_playwright

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "degree_requirements.json"
CATALOG_BASE = "https://catalog.vt.edu"
PROGRAMS_INDEX = f"{CATALOG_BASE}/undergraduate/"

# Known program URL patterns (manually verified for seed data)
KNOWN_PROGRAMS = {
    "CS": "/undergraduate/college-engineering/computer-science/computer-science-bs/",
    "ECE": "/undergraduate/college-engineering/electrical-computer-engineering/electrical-engineering-bsee/",
    "ME": "/undergraduate/college-engineering/mechanical-engineering/mechanical-engineering-bsme/",
    "BIOL": "/undergraduate/college-science/biological-sciences/biological-sciences-bs/",
    "PSYC": "/undergraduate/college-science/psychology/psychology-bs/",
    "CMDA": "/undergraduate/college-science/computational-modeling-data-analytics/",
    "MATH": "/undergraduate/college-science/mathematics/mathematics-bs/",
    "STAT": "/undergraduate/college-science/statistics/statistics-bs/",
    "PHYS": "/undergraduate/college-science/physics/physics-bs/",
    "CHEM": "/undergraduate/college-science/chemistry/chemistry-bs/",
    "FIN": "/undergraduate/pamplin-college-business/finance/finance-bsb/",
    "MGT": "/undergraduate/pamplin-college-business/management/management-bsb/",
    "MKTG": "/undergraduate/pamplin-college-business/marketing/marketing-management-bsb/",
    "ACIS": "/undergraduate/pamplin-college-business/accounting-information-systems/accounting-information-systems-bsb/",
    "ISE": "/undergraduate/college-engineering/industrial-systems-engineering/industrial-systems-engineering-bsise/",
}


def get_gemini_client():
    """Initialize Gemini client for AI-assisted parsing."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠ GEMINI_API_KEY not set - AI parsing unavailable")
        return None
    from google import genai
    return genai.Client(api_key=api_key)


PARSE_PROMPT = """You are parsing a Virginia Tech degree program page from catalog.vt.edu.

Given the page content below, extract the degree requirements as structured JSON.
Be thorough and accurate. Only include course codes you can actually find in the text.

Return this exact JSON structure:
{
  "major_code": "CS",
  "major_name": "Computer Science",
  "degree": "BS",
  "college": "College of Engineering",
  "total_credits": 120,
  "core_courses": ["CS 1114", "CS 2114"],
  "choice_requirements": {
    "requirement_name": {
      "pick": 1,
      "from": ["MATH 2534", "MATH 3034"]
    }
  },
  "elective_requirements": {
    "category_name": {
      "min_courses": 3,
      "min_credits": 9,
      "filter": "CS 3000+"
    }
  },
  "math_requirements": ["MATH 1225", "MATH 1226"],
  "science_requirements": {
    "required": [
      {"name": "Physics", "courses": ["PHYS 2305", "PHYS 2306"]}
    ]
  },
  "pathways_credits": 27,
  "recommended_sequence": {
    "fall_1": ["CS 1114", "MATH 1225"],
    "spring_1": ["CS 2114", "MATH 1226"]
  },
  "difficulty_ratings": {}
}

RULES:
1. Course codes look like "CS 1114", "MATH 2534", "ECE 2004" (2-4 letter dept + space + 4 digit number)
2. "core_courses" = mandatory courses every student in this major must take
3. "choice_requirements" = places where students pick one/some from a list (e.g., "select one of...")
4. "elective_requirements" = categories where students need X courses (e.g., "4 CS electives at 3000+ level")
5. For the filter field, use format like "CS 3000+" or "STEM 2000+"
6. If you find a recommended course sequence (by semester/year), include it
7. If total credits aren't explicitly stated, use 120 as default
8. Leave difficulty_ratings as empty dict - we fill those separately
9. For science requirements, note if it's "choose one sequence" vs "all required"

PAGE CONTENT:
"""


async def scrape_program_page(page, url: str, gemini_client) -> dict:
    """Scrape a single program page and parse with Gemini."""
    try:
        await page.goto(CATALOG_BASE + url, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_timeout(3000)

        # Extract page text content
        content = await page.evaluate("""() => {
            // Get main content area
            const main = document.querySelector('#main-content, .page_content, article, main');
            if (!main) return document.body.innerText;

            // Get all text, preserving structure
            return main.innerText;
        }""")

        if not content or len(content) < 100:
            return None

        # Also try to extract structured data from tables
        table_data = await page.evaluate("""() => {
            const tables = document.querySelectorAll('table');
            const results = [];
            tables.forEach(t => {
                const rows = [];
                t.querySelectorAll('tr').forEach(tr => {
                    const cells = [];
                    tr.querySelectorAll('td, th').forEach(td => {
                        cells.push(td.innerText.trim());
                    });
                    if (cells.length > 0) rows.push(cells);
                });
                if (rows.length > 0) results.push(rows);
            });
            return results;
        }""")

        # Combine content
        full_content = content[:8000]
        if table_data:
            full_content += "\n\nTABLE DATA:\n"
            for table in table_data[:5]:  # Max 5 tables
                for row in table[:30]:  # Max 30 rows per table
                    full_content += " | ".join(row) + "\n"

        # Use Gemini to parse
        if gemini_client:
            try:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=PARSE_PROMPT + full_content[:10000],
                    config={
                        "response_mime_type": "application/json",
                        "temperature": 0.1
                    }
                )
                result = json.loads(response.text)
                return result
            except Exception as e:
                print(f"    Gemini parse failed: {str(e)[:60]}")

        # Fallback: basic regex extraction
        return parse_basic(content, url)

    except Exception as e:
        print(f"    Scrape failed: {str(e)[:60]}")
        return None


def parse_basic(content: str, url: str) -> dict:
    """Basic regex-based parsing fallback when Gemini isn't available."""
    # Extract course codes
    codes = re.findall(r'([A-Z]{2,4})\s+(\d{4})', content)
    unique_courses = list(dict.fromkeys(f"{d} {n}" for d, n in codes))

    # Try to extract program name from URL
    parts = url.strip('/').split('/')
    name = parts[-1].replace('-', ' ').title() if parts else "Unknown"

    # Guess major code from URL or first course
    major_code = ""
    if unique_courses:
        major_code = unique_courses[0].split()[0]

    # Try to find total credits
    credits_match = re.search(r'(\d{2,3})\s*(?:total\s*)?credits?\s*(?:required|minimum|total)', content, re.I)
    total_credits = int(credits_match.group(1)) if credits_match else 120

    # Separate core from electives (heuristic: courses mentioned first are more likely core)
    core = unique_courses[:12] if len(unique_courses) > 12 else unique_courses

    return {
        "major_code": major_code,
        "major_name": name,
        "degree": "BS",
        "college": "",
        "total_credits": total_credits,
        "core_courses": core,
        "choice_requirements": {},
        "elective_requirements": {},
        "math_requirements": [c for c in unique_courses if c.startswith("MATH")],
        "science_requirements": {},
        "pathways_credits": 0,
        "recommended_sequence": {},
        "difficulty_ratings": {},
    }


async def discover_programs(page) -> list:
    """Discover all undergraduate program URLs from the catalog index."""
    print("Discovering program URLs from catalog index...")

    programs = []

    # Navigate to undergraduate programs index
    await page.goto(f"{CATALOG_BASE}/undergraduate/", wait_until='domcontentloaded', timeout=60000)
    await page.wait_for_timeout(3000)

    # Get all college links
    college_links = await page.evaluate("""() => {
        const links = Array.from(document.querySelectorAll('a[href*="/undergraduate/"]'));
        return links
            .map(a => ({
                href: a.getAttribute('href'),
                text: a.innerText.trim()
            }))
            .filter(l => l.href && !l.href.includes('course-descriptions')
                         && !l.href.endsWith('/undergraduate/')
                         && l.text.length > 3);
    }""")

    # Visit each college page to find program links
    seen = set()
    for link in college_links:
        href = link['href']
        if href in seen or not href.startswith('/undergraduate/'):
            continue
        seen.add(href)

        try:
            await page.goto(CATALOG_BASE + href, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(2000)

            # Find links to BS/BA program pages
            program_links = await page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a'));
                return links
                    .map(a => ({
                        href: a.getAttribute('href') || '',
                        text: a.innerText.trim()
                    }))
                    .filter(l => l.href.match(/-(bs|ba|bsb|bse|barch|bfa|bla|bmus|bsba|bsee|bsme|bsce|bsche|bsise|bsaoe|bsbse)\\/?$/i)
                                 || l.text.match(/Bachelor of/i));
            }""")

            for prog in program_links:
                if prog['href'] and prog['href'] not in seen:
                    seen.add(prog['href'])
                    programs.append({
                        "url": prog['href'],
                        "name": prog['text'],
                    })

        except Exception as e:
            print(f"  Error visiting {href}: {str(e)[:40]}")

        await asyncio.sleep(0.3)

    print(f"Discovered {len(programs)} program pages")
    return programs


async def main():
    parser = argparse.ArgumentParser(description='Scrape VT degree requirements')
    parser.add_argument('--major', type=str, help='Scrape specific major (e.g., CS)')
    parser.add_argument('--test', action='store_true', help='Test with 5 known majors')
    parser.add_argument('--discover', action='store_true', help='Discover all program URLs')
    args = parser.parse_args()

    gemini_client = get_gemini_client()

    # Load existing data
    existing = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            existing = json.load(f)

    programs = existing.get("programs", {})

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()

        if args.major:
            # Scrape specific major
            major = args.major.upper()
            url = KNOWN_PROGRAMS.get(major)
            if not url:
                print(f"Unknown program URL for {major}. Add it to KNOWN_PROGRAMS dict.")
                return
            print(f"Scraping {major}...")
            result = await scrape_program_page(page, url, gemini_client)
            if result:
                result["catalog_url"] = CATALOG_BASE + url
                # Preserve existing concentrations if any
                if major in programs and "concentrations" in programs[major]:
                    result["concentrations"] = programs[major]["concentrations"]
                programs[major] = result
                print(f"  ✓ {result.get('major_name', major)}: {len(result.get('core_courses', []))} core courses")

        elif args.test:
            # Test with known majors
            test_majors = ["CS", "ECE", "ME", "BIOL", "FIN"]
            for major in test_majors:
                url = KNOWN_PROGRAMS.get(major)
                if not url:
                    continue
                print(f"Scraping {major}...")
                result = await scrape_program_page(page, url, gemini_client)
                if result:
                    result["catalog_url"] = CATALOG_BASE + url
                    if major in programs and "concentrations" in programs[major]:
                        result["concentrations"] = programs[major]["concentrations"]
                    programs[major] = result
                    print(f"  ✓ {result.get('major_name', major)}: {len(result.get('core_courses', []))} core courses")
                await asyncio.sleep(1)

        elif args.discover:
            # Discover all programs
            discovered = await discover_programs(page)
            print("\nDiscovered programs:")
            for prog in discovered:
                print(f"  {prog['name']}: {prog['url']}")

        else:
            # Scrape all known programs
            for major, url in KNOWN_PROGRAMS.items():
                if major in programs and len(programs[major].get("core_courses", [])) > 3:
                    print(f"Skipping {major} (already has data)")
                    continue
                print(f"Scraping {major}...")
                result = await scrape_program_page(page, url, gemini_client)
                if result:
                    result["catalog_url"] = CATALOG_BASE + url
                    if major in programs and "concentrations" in programs[major]:
                        result["concentrations"] = programs[major]["concentrations"]
                    programs[major] = result
                    print(f"  ✓ {result.get('major_name', major)}: {len(result.get('core_courses', []))} core courses")
                await asyncio.sleep(1)

        await browser.close()

    # Save results
    existing["programs"] = programs
    existing["metadata"] = existing.get("metadata", {})
    existing["metadata"]["last_updated"] = __import__('datetime').datetime.now().isoformat()
    existing["metadata"]["total_programs"] = len(programs)
    existing["metadata"]["source"] = "catalog.vt.edu + gemini"

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(existing, f, indent=2)

    print(f"\n✓ Saved {len(programs)} programs to {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
