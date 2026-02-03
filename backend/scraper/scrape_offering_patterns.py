#!/usr/bin/env python3
"""
VT Course Offering Pattern Scraper
====================================
Scrapes the VT Timetable of Classes to determine when courses are typically offered.
Checks multiple past terms to build offering patterns (Fall, Spring, Summer).

Usage:
    python scrape_offering_patterns.py              # Scrape all subjects
    python scrape_offering_patterns.py --subject CS  # Scrape specific subject
"""

import asyncio
import json
import re
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# VT Timetable endpoint
TIMETABLE_URL = "https://banweb.banner.vt.edu/ssb/prod/HZSKVTSC.P_ProcRequest"

# Terms to check (YYYYMM format: 08=Fall, 01=Spring, 06=Summer)
TERMS = [
    ("202308", "Fall"),    # Fall 2023
    ("202401", "Spring"),  # Spring 2024
    ("202406", "Summer"),  # Summer 2024
    ("202408", "Fall"),    # Fall 2024
    ("202501", "Spring"),  # Spring 2025
]

COURSES_FILE = Path(__file__).parent.parent / "data" / "courses.json"


def get_all_subjects():
    """Get list of all subjects from courses.json."""
    if COURSES_FILE.exists():
        with open(COURSES_FILE) as f:
            data = json.load(f)
        courses = data.get("courses", data)
        subjects = set()
        for code in courses:
            parts = code.split()
            if parts:
                subjects.add(parts[0])
        return sorted(subjects)
    return []


async def scrape_timetable_term(session, term_code: str, subject: str) -> list:
    """Scrape one subject for one term from the VT Timetable.

    Uses HTTP POST to the Banner timetable endpoint.
    Returns list of course codes offered.
    """
    import aiohttp

    data = {
        "CAMPUS": "0",
        "TERMYEAR": term_code,
        "CORE_CODE": "AR%",
        "subj_code": subject,
        "SCHDTYPE": "%",
        "CRESSION": "%",
        "crn": "",
        "open_only": "",
        "sess_code": "%",
        "BTN_PRESSED": "FIND+class+sections",
        "diession": "N",
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        async with session.post(TIMETABLE_URL, data=data, headers=headers, timeout=30) as resp:
            html = await resp.text()

        # Parse course codes from the response HTML
        # The timetable returns an HTML table with course info
        codes = set()
        # Match patterns like "CS 1114" in the HTML
        for match in re.finditer(r'<td[^>]*>(' + subject + r')\s*</td>\s*<td[^>]*>(\d{4})', html):
            code = f"{match.group(1)} {match.group(2)}"
            codes.add(code)

        # Also try a more general pattern
        for match in re.finditer(r'(' + subject + r')\s+(\d{4})', html):
            code = f"{match.group(1)} {match.group(2)}"
            codes.add(code)

        return list(codes)

    except Exception as e:
        print(f"    Error scraping {subject} for {term_code}: {str(e)[:40]}")
        return []


async def main():
    parser = argparse.ArgumentParser(description='Scrape VT course offering patterns')
    parser.add_argument('--subject', type=str, help='Scrape specific subject (e.g., CS)')
    args = parser.parse_args()

    import aiohttp

    # Load existing courses
    if not COURSES_FILE.exists():
        print("courses.json not found!")
        return

    with open(COURSES_FILE) as f:
        data = json.load(f)
    courses = data.get("courses", data)

    if args.subject:
        subjects = [args.subject.upper()]
    else:
        subjects = get_all_subjects()

    print(f"Scraping offering patterns for {len(subjects)} subjects across {len(TERMS)} terms...")

    # Track which terms each course is offered
    offering_map = defaultdict(set)

    async with aiohttp.ClientSession() as session:
        for i, subject in enumerate(subjects):
            print(f"[{i+1}/{len(subjects)}] {subject}...", end=" ", flush=True)

            for term_code, season in TERMS:
                offered = await scrape_timetable_term(session, term_code, subject)
                for code in offered:
                    offering_map[code].add(season)

                await asyncio.sleep(0.2)  # Rate limit

            # Count courses updated for this subject
            subject_courses = [c for c in offering_map if c.startswith(subject + " ")]
            print(f"{len(subject_courses)} courses found")

            # Save progress every 20 subjects
            if (i + 1) % 20 == 0:
                _save_progress(courses, offering_map, data)

    # Final save
    _save_progress(courses, offering_map, data)
    print(f"\n✓ Updated offering patterns for {len(offering_map)} courses")


def _save_progress(courses, offering_map, data):
    """Save current progress to courses.json."""
    updated = 0
    for code, seasons in offering_map.items():
        if code in courses:
            courses[code]["typically_offered"] = sorted(list(seasons))
            updated += 1

    data["courses"] = courses
    data["metadata"] = data.get("metadata", {})
    data["metadata"]["offering_patterns_updated"] = __import__('datetime').datetime.now().isoformat()

    with open(COURSES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"   [Progress saved: {updated} courses updated]")


if __name__ == "__main__":
    asyncio.run(main())
