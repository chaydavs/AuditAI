"""
VT Course Catalog Scraper
=========================
Scrapes course data from Virginia Tech's course catalog.
Run: python scrape_vt_courses.py
"""

import json
import re
import time
from pathlib import Path

# Try to import requests, install if not available
try:
    import requests
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "requests"])
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent / "data"
COURSES_FILE = DATA_DIR / "courses.json"

# VT Course Catalog URLs
CATALOG_BASE = "https://catalog.vt.edu"

# CS Department courses
CS_COURSES_URL = f"{CATALOG_BASE}/undergraduate/course-descriptions/cs/"
MATH_COURSES_URL = f"{CATALOG_BASE}/undergraduate/course-descriptions/math/"
STAT_COURSES_URL = f"{CATALOG_BASE}/undergraduate/course-descriptions/stat/"
PHYS_COURSES_URL = f"{CATALOG_BASE}/undergraduate/course-descriptions/phys/"
ENGL_COURSES_URL = f"{CATALOG_BASE}/undergraduate/course-descriptions/engl/"

# Known prerequisites from VT CS checksheet (hardcoded for accuracy)
KNOWN_PREREQS = {
    # CS Core
    "CS 1114": [],
    "CS 1044": [],
    "CS 1064": [],
    "CS 2104": ["CS 1114"],
    "CS 2114": ["CS 1114"],
    "CS 2505": ["CS 1114"],
    "CS 2506": ["CS 2505", "CS 2114"],
    "CS 3114": ["CS 2114", "CS 2505"],
    "CS 3214": ["CS 2506", "CS 3114"],
    "CS 3304": ["CS 2114"],
    "CS 4104": ["CS 3114", "MATH 2114"],

    # CS Electives
    "CS 3414": ["CS 2114", "MATH 2114"],
    "CS 3424": ["CS 2114"],
    "CS 3514": ["CS 2506"],
    "CS 3604": ["CS 2114"],
    "CS 3654": ["CS 2114"],
    "CS 3704": ["CS 2114"],
    "CS 3714": ["CS 2114"],
    "CS 3724": ["CS 2114"],
    "CS 3744": ["CS 2114"],
    "CS 3754": ["CS 2114"],
    "CS 4114": ["CS 3214"],
    "CS 4124": ["CS 3114", "STAT 3006"],
    "CS 4234": ["CS 3214"],
    "CS 4254": ["CS 3214"],
    "CS 4264": ["CS 3214"],
    "CS 4274": ["CS 3214"],
    "CS 4284": ["CS 3214"],
    "CS 4414": ["CS 3214"],
    "CS 4504": ["CS 3214"],
    "CS 4604": ["CS 3114"],
    "CS 4624": ["CS 3114"],
    "CS 4634": ["CS 3114"],
    "CS 4644": ["CS 2114"],
    "CS 4654": ["CS 2114"],
    "CS 4664": ["CS 3114"],
    "CS 4704": ["CS 3114"],
    "CS 4784": ["CS 3114"],
    "CS 4804": ["CS 3114"],
    "CS 4824": ["CS 3114", "MATH 2114"],
    "CS 4884": ["CS 3114"],
    "CS 4944": ["CS 3214"],
    "CS 4974": [],
    "CS 4994": [],

    # Math
    "MATH 1225": [],
    "MATH 1226": ["MATH 1225"],
    "MATH 2114": ["MATH 1226"],
    "MATH 2204": ["MATH 1226"],
    "MATH 2214": ["MATH 1226"],
    "MATH 2534": ["MATH 1226"],
    "MATH 3134": ["MATH 1226"],
    "MATH 3144": ["MATH 2114"],
    "MATH 4144": ["MATH 2114"],
    "MATH 4175": ["MATH 3134"],
    "MATH 4176": ["MATH 4175"],

    # Stats
    "STAT 3006": ["MATH 1226"],
    "STAT 3104": ["STAT 3006"],
    "STAT 3704": ["STAT 3006"],
    "STAT 4204": ["STAT 3006"],
    "STAT 4504": ["STAT 3006"],
    "STAT 4524": ["STAT 3006"],
    "STAT 4604": ["STAT 3006"],
    "STAT 4705": ["STAT 3006"],
    "STAT 4706": ["STAT 4705"],

    # Physics
    "PHYS 2305": ["MATH 1225"],
    "PHYS 2306": ["PHYS 2305", "MATH 1226"],

    # General
    "ENGL 1105": [],
    "ENGL 1106": ["ENGL 1105"],
    "COMM 1016": [],
}

# Course difficulty ratings (1-5 based on student feedback)
DIFFICULTY_RATINGS = {
    "CS 1114": 2, "CS 1064": 1, "CS 2104": 2, "CS 2114": 3,
    "CS 2505": 3, "CS 2506": 4, "CS 3114": 4, "CS 3214": 5,
    "CS 3304": 3, "CS 4104": 4, "CS 3414": 3, "CS 4114": 4,
    "CS 4124": 4, "CS 4254": 3, "CS 4264": 3, "CS 4604": 3,
    "CS 4804": 3, "CS 4824": 4, "MATH 1225": 3, "MATH 1226": 3,
    "MATH 2114": 3, "MATH 2204": 3, "MATH 3134": 3, "STAT 3006": 2,
    "PHYS 2305": 3, "PHYS 2306": 3,
}

# Categories
def get_category(code):
    dept = code.split()[0]
    num = int(code.split()[1]) if len(code.split()) > 1 else 0

    if dept == "CS":
        if code in ["CS 1114", "CS 2104", "CS 2114", "CS 2505", "CS 2506",
                    "CS 3114", "CS 3214", "CS 3304", "CS 4104"]:
            return "cs_core"
        return "cs_elective"
    elif dept == "MATH":
        return "math"
    elif dept == "STAT":
        return "math"
    elif dept == "PHYS":
        return "science"
    elif dept == "CHEM":
        return "science"
    elif dept == "BIOL":
        return "science"
    elif dept in ["ENGL", "COMM", "PHIL", "HIST", "PSYC", "ECON", "MUSI", "ART"]:
        return "pathway"
    return "other"


def scrape_department_courses(url, dept_code):
    """Scrape courses from a VT catalog department page"""
    courses = {}

    try:
        print(f"Fetching {dept_code} courses from {url}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find course blocks
        course_blocks = soup.find_all('div', class_='courseblock')

        for block in course_blocks:
            try:
                # Get course title (contains code and name)
                title_elem = block.find('p', class_='courseblocktitle')
                if not title_elem:
                    continue

                title_text = title_elem.get_text(strip=True)

                # Parse: "CS 1114. Introduction to Software Design. (3H,3C)"
                match = re.match(r'([A-Z]+\s*\d+)[.\s]+(.+?)\.\s*\((\d+)H,(\d+)C\)', title_text)
                if not match:
                    # Try alternate format
                    match = re.match(r'([A-Z]+\s*\d+)[.\s]+(.+)', title_text)
                    if match:
                        code = match.group(1).strip()
                        code = re.sub(r'(\d)', r' \1', code, count=1).strip()  # Add space
                        code = re.sub(r'\s+', ' ', code)  # Normalize spaces
                        name = match.group(2).strip().rstrip('.')
                        credits = 3
                    else:
                        continue
                else:
                    code = match.group(1).strip()
                    code = re.sub(r'(\d)', r' \1', code, count=1).strip()
                    code = re.sub(r'\s+', ' ', code)
                    name = match.group(2).strip()
                    credits = int(match.group(4))

                # Get description
                desc_elem = block.find('p', class_='courseblockdesc')
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                # Clean up description - extract prereqs if mentioned
                prereqs = KNOWN_PREREQS.get(code, [])

                # Look for prerequisite info in description
                if not prereqs and description:
                    prereq_match = re.search(r'Pre(?:requisite)?s?:\s*([^.]+)', description, re.IGNORECASE)
                    if prereq_match:
                        prereq_text = prereq_match.group(1)
                        # Extract course codes
                        found_prereqs = re.findall(r'([A-Z]{2,4}\s*\d{4})', prereq_text)
                        prereqs = [re.sub(r'(\d)', r' \1', p, count=1).strip() for p in found_prereqs]
                        prereqs = [re.sub(r'\s+', ' ', p) for p in prereqs]

                courses[code] = {
                    "name": name,
                    "credits": credits,
                    "prereqs": prereqs,
                    "coreqs": [],
                    "description": description[:500] if description else "",
                    "category": get_category(code),
                    "difficulty": DIFFICULTY_RATINGS.get(code, 3),
                    "workload": DIFFICULTY_RATINGS.get(code, 3),
                    "tags": [],
                    "professors": [],
                    "typically_offered": ["Fall", "Spring"],
                    "required_for": ["cs_major"] if code in [
                        "CS 1114", "CS 2104", "CS 2114", "CS 2505", "CS 2506",
                        "CS 3114", "CS 3214", "CS 3304", "CS 4104",
                        "MATH 1225", "MATH 1226", "MATH 2114", "MATH 3134",
                        "STAT 3006", "PHYS 2305"
                    ] else []
                }

            except Exception as e:
                print(f"  Error parsing course: {e}")
                continue

        print(f"  Found {len(courses)} {dept_code} courses")
        return courses

    except Exception as e:
        print(f"  Error fetching {dept_code}: {e}")
        return {}


def add_manual_courses(courses):
    """Add manually curated courses with accurate info"""

    manual_courses = {
        # Pathways
        "ENGL 1105": {
            "name": "First-Year Writing",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 1, "workload": 2,
            "tags": ["writing", "easy", "pathway"],
            "description": "College-level writing and rhetoric.",
            "professors": [{"name": "Various", "rating": 4.0, "avgGPA": 3.3}],
            "typically_offered": ["Fall", "Spring", "Summer"],
            "required_for": ["all_majors"]
        },
        "COMM 1016": {
            "name": "Introduction to Communication",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 1, "workload": 1,
            "tags": ["speaking", "easy", "pathway"],
            "description": "Public speaking and communication fundamentals.",
            "professors": [{"name": "Various", "rating": 4.2, "avgGPA": 3.5}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "PHIL 1304": {
            "name": "Ethics and Social Philosophy",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 2, "workload": 2,
            "tags": ["philosophy", "ethics", "pathway"],
            "description": "Introduction to ethical theory and social philosophy.",
            "professors": [{"name": "Various", "rating": 4.1, "avgGPA": 3.2}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "MUSI 1004": {
            "name": "Music Appreciation",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 1, "workload": 1,
            "tags": ["music", "easy", "fun", "pathway"],
            "description": "Introduction to music listening and appreciation.",
            "professors": [{"name": "Various", "rating": 4.6, "avgGPA": 3.7}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "PSYC 1004": {
            "name": "Introductory Psychology",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 1, "workload": 1,
            "tags": ["psychology", "easy", "interesting", "pathway"],
            "description": "Introduction to psychological science.",
            "professors": [{"name": "Various", "rating": 4.4, "avgGPA": 3.4}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "ECON 2005": {
            "name": "Principles of Economics",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 2, "workload": 2,
            "tags": ["economics", "useful", "pathway"],
            "description": "Microeconomics and macroeconomics principles.",
            "professors": [{"name": "Various", "rating": 4.0, "avgGPA": 3.0}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "HIST 1115": {
            "name": "US History to 1865",
            "credits": 3, "prereqs": [], "coreqs": [],
            "category": "pathway", "difficulty": 2, "workload": 2,
            "tags": ["history", "pathway"],
            "description": "American history from colonization to Civil War.",
            "professors": [{"name": "Various", "rating": 4.2, "avgGPA": 3.3}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },

        # Sciences
        "CHEM 1035": {
            "name": "General Chemistry",
            "credits": 4, "prereqs": [], "coreqs": [],
            "category": "science", "difficulty": 2, "workload": 3,
            "tags": ["chemistry", "lab", "science"],
            "description": "Introductory chemistry with laboratory.",
            "professors": [{"name": "Various", "rating": 4.0, "avgGPA": 3.0}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "BIOL 1105": {
            "name": "Principles of Biology",
            "credits": 4, "prereqs": [], "coreqs": [],
            "category": "science", "difficulty": 2, "workload": 2,
            "tags": ["biology", "lab", "science"],
            "description": "Introductory biology with laboratory.",
            "professors": [{"name": "Various", "rating": 4.2, "avgGPA": 3.2}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
        "GEOS 1004": {
            "name": "Physical Geology",
            "credits": 4, "prereqs": [], "coreqs": [],
            "category": "science", "difficulty": 2, "workload": 2,
            "tags": ["geology", "lab", "easy-science"],
            "description": "Introduction to physical geology.",
            "professors": [{"name": "Various", "rating": 4.3, "avgGPA": 3.3}],
            "typically_offered": ["Fall", "Spring"],
            "required_for": []
        },
    }

    courses.update(manual_courses)
    return courses


def main():
    """Main scraping function"""
    print("=" * 60)
    print("VT Course Catalog Scraper")
    print("=" * 60)

    all_courses = {}

    # Scrape each department
    departments = [
        (CS_COURSES_URL, "CS"),
        (MATH_COURSES_URL, "MATH"),
        (STAT_COURSES_URL, "STAT"),
        (PHYS_COURSES_URL, "PHYS"),
    ]

    for url, dept in departments:
        courses = scrape_department_courses(url, dept)
        all_courses.update(courses)
        time.sleep(1)  # Be nice to the server

    # Add manual courses (pathways, etc.)
    all_courses = add_manual_courses(all_courses)

    # Ensure required courses have proper data
    for code, prereqs in KNOWN_PREREQS.items():
        if code in all_courses:
            all_courses[code]["prereqs"] = prereqs
        else:
            # Add missing course with minimal info
            all_courses[code] = {
                "name": code,
                "credits": 3,
                "prereqs": prereqs,
                "coreqs": [],
                "category": get_category(code),
                "difficulty": DIFFICULTY_RATINGS.get(code, 3),
                "workload": DIFFICULTY_RATINGS.get(code, 3),
                "tags": [],
                "professors": [],
                "typically_offered": ["Fall", "Spring"],
                "required_for": [],
                "description": ""
            }

    print(f"\nTotal courses scraped: {len(all_courses)}")

    # Save to JSON
    DATA_DIR.mkdir(exist_ok=True)

    # Load existing file to preserve metadata
    existing_data = {"metadata": {}, "courses": {}, "degree_requirements": {}}
    if COURSES_FILE.exists():
        try:
            with open(COURSES_FILE, 'r') as f:
                existing_data = json.load(f)
        except:
            pass

    existing_data["courses"] = all_courses
    existing_data["metadata"]["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    existing_data["metadata"]["source"] = "VT Course Catalog + Manual Curation"
    existing_data["metadata"]["total_courses"] = len(all_courses)

    with open(COURSES_FILE, 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"Saved to {COURSES_FILE}")
    print("=" * 60)

    return all_courses


if __name__ == "__main__":
    main()
