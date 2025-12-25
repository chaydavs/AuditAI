#!/usr/bin/env python3
"""
Fix and merge course data - combine scraped data with existing good data
"""

import json
import re
from pathlib import Path

# Load existing good data
EXISTING_FILE = Path("data/courses.json")
SCRAPED_FILE = Path("data/courses_scraped.json")
OUTPUT_FILE = Path("data/courses.json")

def determine_category(code, name=""):
    """Determine course category based on code"""
    parts = code.split()
    if len(parts) < 2:
        return "elective"

    subject = parts[0]
    try:
        num = int(parts[1])
    except:
        return "elective"

    name_lower = name.lower()

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


def fix_name(code, scraped_name):
    """Fix course name - if it's just the code, try to clean it up"""
    # If name is just the course code, return a generic name
    if scraped_name == code or not scraped_name:
        return f"{code.split()[0]} Course"

    # Clean up the name
    name = scraped_name.strip()
    # Remove leading dashes
    name = re.sub(r'^[-–]\s*', '', name)
    # Remove credits info
    name = re.sub(r'\s*\(\d+\s*credits?\)', '', name, flags=re.I)
    name = re.sub(r'\s*\(\d+H,\s*\d+C\)', '', name)

    return name.strip() or f"{code.split()[0]} Course"


def main():
    # Load existing data (has good names)
    existing = {}
    if EXISTING_FILE.exists():
        with open(EXISTING_FILE) as f:
            existing = json.load(f)

    print(f"Loaded {len(existing)} existing courses")

    # Load scraped data
    scraped = {}
    if SCRAPED_FILE.exists():
        with open(SCRAPED_FILE) as f:
            scraped = json.load(f)

    print(f"Loaded {len(scraped)} scraped courses")

    # Merge: prefer existing data, but add new courses from scraped
    merged = {}

    # First, add all existing (they have correct names)
    for code, data in existing.items():
        merged[code] = data

    # Then, add scraped courses that don't exist
    added = 0
    for code, data in scraped.items():
        if code not in merged:
            # Fix the name if it's just the course code
            name = fix_name(code, data.get('name', ''))

            merged[code] = {
                "name": name,
                "credits": data.get('credits', 3),
                "prereqs": data.get('prereqs', []),
                "category": determine_category(code, name),
                "description": data.get('description', '')[:200]
            }
            added += 1

    print(f"Added {added} new courses from scraped data")
    print(f"Total: {len(merged)} courses")

    # Sort by code
    sorted_courses = dict(sorted(merged.items()))

    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted_courses, f, indent=2)

    print(f"Saved to {OUTPUT_FILE}")

    # Summary by category
    cats = {}
    for code, data in sorted_courses.items():
        cat = data.get('category', 'unknown')
        cats[cat] = cats.get(cat, 0) + 1

    print("\nBy category:")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
