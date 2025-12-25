"""
VT Timetable of Classes Scraper
================================
Scrapes Virginia Tech's Timetable of Classes for current course offerings.
This is easier to scrape than the catalog as it has a more predictable structure.

Timetable URL: https://banweb.banner.vt.edu/ssb/prod/HZSKVTSC.P_ProcRequest

Usage:
    python vt_timetable_scraper.py --term 202501 --subject CS
"""

import json
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup

# VT Timetable endpoints
TIMETABLE_URL = "https://banweb.banner.vt.edu/ssb/prod/HZSKVTSC.P_ProcRequest"
TIMETABLE_FORM_URL = "https://banweb.banner.vt.edu/ssb/prod/HZSKVTSC.P_DispRequest"

OUTPUT_DIR = Path(__file__).parent.parent / "data"

# Known VT CS course prerequisites (manually curated for accuracy)
KNOWN_PREREQS = {
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
    "CS 3414": ["CS 2114", "MATH 2114"],
    "CS 4104": ["CS 3114", "MATH 2114"],
    "CS 4114": ["CS 3214"],
    "CS 4124": ["CS 3114", "STAT 3006"],
    "CS 4254": ["CS 3214"],
    "CS 4264": ["CS 3214"],
    "CS 4284": ["CS 3214"],
    "CS 4604": ["CS 3114"],
    "CS 4624": ["CS 3114"],
    "CS 4644": ["CS 2114"],
    "CS 4804": ["CS 3114"],
    "CS 4824": ["CS 3114", "MATH 2114"],
    "CS 4944": ["CS 3214"],
    "MATH 1225": [],
    "MATH 1226": ["MATH 1225"],
    "MATH 2114": ["MATH 1226"],
    "MATH 2204": ["MATH 1226"],
    "MATH 3134": ["MATH 1226"],
    "STAT 3006": ["MATH 1226"],
    "STAT 4705": ["STAT 3006"],
    "STAT 4706": ["STAT 3006"],
    "PHYS 2305": ["MATH 1225"],
    "PHYS 2306": ["PHYS 2305", "MATH 1226"],
}

# Core courses for CS major
CS_CORE_COURSES = {
    "CS 1114", "CS 2104", "CS 2114", "CS 2505", "CS 2506",
    "CS 3114", "CS 3214", "CS 3304", "CS 4104"
}

# Difficulty ratings (1-5, higher = harder)
DIFFICULTY_RATINGS = {
    "CS 1114": 2, "CS 1044": 2, "CS 1064": 1,
    "CS 2104": 2, "CS 2114": 3, "CS 2505": 3, "CS 2506": 4,
    "CS 3114": 4, "CS 3214": 5, "CS 3304": 3, "CS 3414": 3,
    "CS 4104": 4, "CS 4114": 4, "CS 4124": 4,
    "CS 4254": 3, "CS 4264": 3, "CS 4284": 4,
    "CS 4604": 3, "CS 4624": 2, "CS 4644": 2,
    "CS 4804": 3, "CS 4824": 4, "CS 4944": 3,
    "MATH 1225": 3, "MATH 1226": 3, "MATH 2114": 3, "MATH 2204": 3,
    "MATH 3134": 3, "STAT 3006": 2,
}

# Workload ratings (1-5, higher = more work)
WORKLOAD_RATINGS = {
    "CS 1114": 2, "CS 1044": 2, "CS 1064": 1,
    "CS 2104": 2, "CS 2114": 4, "CS 2505": 3, "CS 2506": 4,
    "CS 3114": 5, "CS 3214": 5, "CS 3304": 3, "CS 3414": 3,
    "CS 4104": 4, "CS 4114": 4, "CS 4124": 4,
    "CS 4254": 3, "CS 4264": 3, "CS 4284": 4,
    "CS 4604": 3, "CS 4624": 2, "CS 4644": 2,
    "CS 4804": 3, "CS 4824": 4, "CS 4944": 3,
}


def scrape_timetable(term: str = "202501", subjects: list[str] = None) -> dict:
    """
    Scrape VT timetable for course information.

    Args:
        term: Term code (e.g., "202501" for Spring 2025)
        subjects: List of subjects to scrape

    Returns:
        Dictionary of courses
    """
    if subjects is None:
        subjects = ['CS', 'MATH', 'STAT', 'PHYS']

    all_courses = {}
    session = requests.Session()

    # Set up headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': TIMETABLE_FORM_URL,
    }

    for subject in subjects:
        print(f"\nScraping {subject}...")

        # Prepare form data for timetable request
        form_data = {
            'CAMPUS': '0',       # All campuses
            'TERMYEAR': term,
            'CORE_CODE': 'AR%',  # All core codes
            'subj_code': subject,
            'SCHDTYPE': '%',     # All schedule types
            'CRESSION': '%',     # All sessions
            'open_only': '',     # Include closed sections
            'BTN_PRESSED': 'FIND class sections',
        }

        try:
            response = session.post(TIMETABLE_URL, data=form_data, headers=headers, timeout=30)

            if response.status_code == 200:
                courses = parse_timetable_html(response.text, subject)
                print(f"  Found {len(courses)} courses")

                for course in courses:
                    code = course['code']
                    if code not in all_courses:
                        all_courses[code] = course
                    else:
                        # Merge professor data
                        existing_profs = {p['name'] for p in all_courses[code].get('professors', [])}
                        for prof in course.get('professors', []):
                            if prof['name'] not in existing_profs:
                                all_courses[code].setdefault('professors', []).append(prof)
            else:
                print(f"  Error: HTTP {response.status_code}")

        except Exception as e:
            print(f"  Error scraping {subject}: {e}")

    return all_courses


def parse_timetable_html(html: str, subject: str) -> list[dict]:
    """Parse VT timetable HTML response."""
    courses = {}
    soup = BeautifulSoup(html, 'html.parser')

    # Find course tables
    tables = soup.find_all('table', class_='dataentrytable')

    for table in tables:
        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 5:
                continue

            try:
                # Extract course info from cells
                # VT timetable format: CRN, Course, Title, Type, Credits, Capacity, Instructor, Days, Begin, End, Location
                text = ' '.join(cell.get_text(strip=True) for cell in cells)

                # Find course code
                code_match = re.search(rf'({subject})\s*(\d{{4}})', text)
                if not code_match:
                    continue

                course_code = f"{code_match.group(1)} {code_match.group(2)}"

                # Find course title (usually in 3rd column)
                title = ""
                if len(cells) >= 3:
                    title = cells[2].get_text(strip=True)[:100]

                # Find credits
                credits = 3
                credits_match = re.search(r'(\d+)\s*(?:cr|CR|Credits?)', text)
                if credits_match:
                    credits = int(credits_match.group(1))

                # Find instructor
                instructor = ""
                for cell in cells:
                    cell_text = cell.get_text(strip=True)
                    # Instructor names usually have format "Last, First" or are in specific column
                    if re.match(r'^[A-Z][a-z]+,\s*[A-Z]', cell_text):
                        instructor = cell_text
                        break

                # Create or update course
                if course_code not in courses:
                    courses[course_code] = create_course_entry(course_code, title, credits, subject)

                # Add professor if found
                if instructor and instructor not in [p['name'] for p in courses[course_code].get('professors', [])]:
                    courses[course_code].setdefault('professors', []).append({
                        'name': instructor,
                        'rating': 0,
                        'avgGPA': 0
                    })

            except Exception as e:
                continue

    return list(courses.values())


def create_course_entry(code: str, name: str, credits: int, subject: str) -> dict:
    """Create a course entry with all metadata."""
    course_num = int(code.split()[1])

    # Determine category
    if subject == 'CS':
        category = 'cs_core' if code in CS_CORE_COURSES else 'cs_elective'
    elif subject in ['MATH', 'STAT']:
        category = 'math'
    elif subject in ['PHYS', 'CHEM', 'BIOL']:
        category = 'science'
    else:
        category = 'pathway'

    # Get prereqs from known list
    prereqs = KNOWN_PREREQS.get(code, [])

    # Get difficulty and workload
    difficulty = DIFFICULTY_RATINGS.get(code, 3)
    workload = WORKLOAD_RATINGS.get(code, 3)

    # Generate tags
    tags = []
    if difficulty >= 4:
        tags.append('heavy')
    if difficulty == 5:
        tags.append('weedout')
    if difficulty <= 2:
        tags.append('easy')
    if 'intro' in name.lower() or course_num < 2000:
        tags.append('intro')
    if category == 'cs_core':
        tags.append('required')

    return {
        "code": code,
        "name": name,
        "credits": credits,
        "prereqs": prereqs,
        "coreqs": [],
        "category": category,
        "difficulty": difficulty,
        "workload": workload,
        "tags": tags,
        "professors": [],
        "description": "",
        "typically_offered": ["Fall", "Spring"],
        "required_for": ["cs_major"] if code in CS_CORE_COURSES else []
    }


def load_known_courses() -> dict:
    """Load comprehensive known course data."""
    return {
        # CS CORE
        "CS 1114": {
            "name": "Introduction to Software Design",
            "credits": 3,
            "prereqs": [],
            "category": "cs_core",
            "difficulty": 2,
            "workload": 2,
            "tags": ["intro", "programming", "java", "required"],
            "description": "Fundamental concepts of programming from an object-oriented perspective.",
            "professors": [
                {"name": "McQuain, W", "rating": 4.2, "avgGPA": 3.1},
                {"name": "Shaffer, C", "rating": 3.8, "avgGPA": 2.9}
            ]
        },
        "CS 1044": {
            "name": "Introduction to Programming in C",
            "credits": 3,
            "prereqs": [],
            "category": "cs_core",
            "difficulty": 2,
            "workload": 2,
            "tags": ["intro", "programming", "c"],
            "description": "Introduction to programming using the C language."
        },
        "CS 1064": {
            "name": "Introduction to Programming in Python",
            "credits": 2,
            "prereqs": [],
            "category": "cs_core",
            "difficulty": 1,
            "workload": 1,
            "tags": ["intro", "python", "easy"],
            "description": "Introduction to programming using Python."
        },
        "CS 2104": {
            "name": "Introduction to Problem Solving in Computer Science",
            "credits": 3,
            "prereqs": ["CS 1114"],
            "category": "cs_core",
            "difficulty": 2,
            "workload": 2,
            "tags": ["theory", "problem-solving", "required"],
            "description": "Problem solving approaches in computer science."
        },
        "CS 2114": {
            "name": "Software Design and Data Structures",
            "credits": 3,
            "prereqs": ["CS 1114"],
            "category": "cs_core",
            "difficulty": 3,
            "workload": 4,
            "tags": ["data-structures", "oop", "heavy", "required"],
            "description": "Object-oriented design, data structures, and algorithms.",
            "professors": [
                {"name": "McQuain, W", "rating": 4.0, "avgGPA": 3.2},
                {"name": "Shaffer, C", "rating": 3.5, "avgGPA": 2.8}
            ]
        },
        "CS 2505": {
            "name": "Introduction to Computer Organization",
            "credits": 3,
            "prereqs": ["CS 1114"],
            "category": "cs_core",
            "difficulty": 3,
            "workload": 3,
            "tags": ["systems", "assembly", "hardware", "required"],
            "description": "Computer organization and assembly language.",
            "professors": [
                {"name": "Butt, A", "rating": 3.7, "avgGPA": 2.9},
                {"name": "Jones, M", "rating": 4.1, "avgGPA": 3.1}
            ]
        },
        "CS 2506": {
            "name": "Introduction to Computer Organization II",
            "credits": 3,
            "prereqs": ["CS 2505", "CS 2114"],
            "category": "cs_core",
            "difficulty": 4,
            "workload": 4,
            "tags": ["systems", "c", "hardware", "heavy", "required"],
            "description": "Advanced computer organization and C programming."
        },
        "CS 3114": {
            "name": "Data Structures and Algorithms",
            "credits": 3,
            "prereqs": ["CS 2114", "CS 2505"],
            "category": "cs_core",
            "difficulty": 4,
            "workload": 5,
            "tags": ["algorithms", "data-structures", "heavy", "weedout", "required"],
            "description": "Advanced data structures, algorithm analysis and design.",
            "professors": [
                {"name": "Back, G", "rating": 4.3, "avgGPA": 3.0},
                {"name": "Shaffer, C", "rating": 3.4, "avgGPA": 2.6}
            ]
        },
        "CS 3214": {
            "name": "Computer Systems",
            "credits": 3,
            "prereqs": ["CS 2506", "CS 3114"],
            "category": "cs_core",
            "difficulty": 5,
            "workload": 5,
            "tags": ["systems", "c", "linux", "very-heavy", "weedout", "required"],
            "description": "Systems programming, concurrency, and operating systems concepts.",
            "professors": [
                {"name": "Back, G", "rating": 4.1, "avgGPA": 2.8}
            ]
        },
        "CS 3304": {
            "name": "Comparative Languages",
            "credits": 3,
            "prereqs": ["CS 2114"],
            "category": "cs_core",
            "difficulty": 3,
            "workload": 3,
            "tags": ["languages", "theory", "required"],
            "description": "Programming language concepts and paradigms."
        },
        "CS 4104": {
            "name": "Data and Algorithm Analysis",
            "credits": 3,
            "prereqs": ["CS 3114", "MATH 2114"],
            "category": "cs_core",
            "difficulty": 4,
            "workload": 4,
            "tags": ["algorithms", "theory", "math-heavy", "required"],
            "description": "Mathematical analysis of algorithms."
        },
        # CS ELECTIVES
        "CS 3414": {
            "name": "Numerical Methods",
            "credits": 3,
            "prereqs": ["CS 2114", "MATH 2114"],
            "category": "cs_elective",
            "difficulty": 3,
            "workload": 3,
            "tags": ["math", "numerical", "matlab"]
        },
        "CS 4114": {
            "name": "Introduction to Operating Systems",
            "credits": 3,
            "prereqs": ["CS 3214"],
            "category": "cs_elective",
            "difficulty": 4,
            "workload": 4,
            "tags": ["systems", "os", "heavy"]
        },
        "CS 4124": {
            "name": "Machine Learning",
            "credits": 3,
            "prereqs": ["CS 3114", "STAT 3006"],
            "category": "cs_elective",
            "difficulty": 4,
            "workload": 4,
            "tags": ["ml", "ai", "python", "hot"],
            "professors": [
                {"name": "Huang, B", "rating": 4.4, "avgGPA": 3.3}
            ]
        },
        "CS 4254": {
            "name": "Computer Network Architecture and Programming",
            "credits": 3,
            "prereqs": ["CS 3214"],
            "category": "cs_elective",
            "difficulty": 3,
            "workload": 3,
            "tags": ["networks", "systems"]
        },
        "CS 4264": {
            "name": "Principles of Computer Security",
            "credits": 3,
            "prereqs": ["CS 3214"],
            "category": "cs_elective",
            "difficulty": 3,
            "workload": 3,
            "tags": ["security", "hot", "industry"]
        },
        "CS 4284": {
            "name": "Systems and Networking Capstone",
            "credits": 3,
            "prereqs": ["CS 3214"],
            "category": "cs_elective",
            "difficulty": 4,
            "workload": 4,
            "tags": ["capstone", "systems", "project"]
        },
        "CS 4604": {
            "name": "Introduction to Data Base Management Systems",
            "credits": 3,
            "prereqs": ["CS 3114"],
            "category": "cs_elective",
            "difficulty": 3,
            "workload": 3,
            "tags": ["databases", "sql", "industry", "easy-elective"],
            "professors": [
                {"name": "Ramakrishnan, N", "rating": 4.5, "avgGPA": 3.3}
            ]
        },
        "CS 4624": {
            "name": "Multimedia, Hypertext, and Information Access",
            "credits": 3,
            "prereqs": ["CS 3114"],
            "category": "cs_elective",
            "difficulty": 2,
            "workload": 2,
            "tags": ["multimedia", "easy-elective"]
        },
        "CS 4644": {
            "name": "Creative Computing Studio",
            "credits": 3,
            "prereqs": ["CS 2114"],
            "category": "cs_elective",
            "difficulty": 2,
            "workload": 2,
            "tags": ["creative", "fun", "easy-elective"]
        },
        "CS 4804": {
            "name": "Introduction to Artificial Intelligence",
            "credits": 3,
            "prereqs": ["CS 3114"],
            "category": "cs_elective",
            "difficulty": 3,
            "workload": 3,
            "tags": ["ai", "theory", "hot"],
            "professors": [
                {"name": "Cao, Y", "rating": 4.4, "avgGPA": 3.4}
            ]
        },
        "CS 4824": {
            "name": "Machine Learning II",
            "credits": 3,
            "prereqs": ["CS 3114", "MATH 2114"],
            "category": "cs_elective",
            "difficulty": 4,
            "workload": 4,
            "tags": ["ml", "ai", "advanced", "heavy"]
        },
        # MATH
        "MATH 1225": {
            "name": "Calculus of a Single Variable",
            "credits": 3,
            "prereqs": [],
            "category": "math",
            "difficulty": 3,
            "workload": 3,
            "tags": ["math", "calculus", "required"]
        },
        "MATH 1226": {
            "name": "Calculus of a Single Variable",
            "credits": 3,
            "prereqs": ["MATH 1225"],
            "category": "math",
            "difficulty": 3,
            "workload": 3,
            "tags": ["math", "calculus", "required"]
        },
        "MATH 2114": {
            "name": "Introduction to Linear Algebra",
            "credits": 3,
            "prereqs": ["MATH 1226"],
            "category": "math",
            "difficulty": 3,
            "workload": 3,
            "tags": ["math", "linear-algebra", "useful", "required"]
        },
        "MATH 2204": {
            "name": "Introduction to Multivariable Calculus",
            "credits": 3,
            "prereqs": ["MATH 1226"],
            "category": "math",
            "difficulty": 3,
            "workload": 3,
            "tags": ["math", "calculus"]
        },
        "MATH 3134": {
            "name": "Applied Combinatorics",
            "credits": 3,
            "prereqs": ["MATH 1226"],
            "category": "math",
            "difficulty": 3,
            "workload": 2,
            "tags": ["math", "discrete", "cs-related", "required"]
        },
        "STAT 3006": {
            "name": "Statistics for Engineers",
            "credits": 3,
            "prereqs": ["MATH 1226"],
            "category": "math",
            "difficulty": 2,
            "workload": 2,
            "tags": ["stats", "easy", "useful", "required"]
        },
        # SCIENCE
        "PHYS 2305": {
            "name": "Foundations of Physics",
            "credits": 4,
            "prereqs": ["MATH 1225"],
            "category": "science",
            "difficulty": 3,
            "workload": 3,
            "tags": ["physics", "lab", "required"]
        },
        "PHYS 2306": {
            "name": "Foundations of Physics",
            "credits": 4,
            "prereqs": ["PHYS 2305", "MATH 1226"],
            "category": "science",
            "difficulty": 3,
            "workload": 3,
            "tags": ["physics", "lab", "e&m"]
        },
        # PATHWAYS
        "ENGL 1105": {
            "name": "First-Year Writing",
            "credits": 3,
            "prereqs": [],
            "category": "pathway",
            "difficulty": 1,
            "workload": 2,
            "tags": ["writing", "easy", "pathway"]
        },
        "COMM 1016": {
            "name": "Introduction to Communication",
            "credits": 3,
            "prereqs": [],
            "category": "pathway",
            "difficulty": 1,
            "workload": 1,
            "tags": ["speaking", "easy", "pathway"]
        },
    }


def save_courses(courses: dict, output_path: Path = None):
    """Save courses to JSON file."""
    if output_path is None:
        output_path = OUTPUT_DIR / "courses.json"

    output_path.parent.mkdir(exist_ok=True)

    # Load existing file to preserve structure
    existing = {}
    if output_path.exists():
        with open(output_path, 'r') as f:
            existing = json.load(f)

    # Merge courses
    existing_courses = existing.get('courses', {})
    for code, data in courses.items():
        if code in existing_courses:
            # Merge - keep existing enriched data
            for key in ['professors', 'description']:
                if existing_courses[code].get(key) and not data.get(key):
                    data[key] = existing_courses[code][key]
        existing_courses[code] = data

    result = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "source": "VT Timetable + Manual Data",
            "total_courses": len(existing_courses)
        },
        "courses": existing_courses
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Saved {len(existing_courses)} courses to {output_path}")
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape VT Timetable')
    parser.add_argument('--term', type=str, default='202501', help='Term code')
    parser.add_argument('--subject', type=str, help='Single subject to scrape')
    parser.add_argument('--known-only', action='store_true', help='Only save known courses')
    parser.add_argument('--output', type=str, help='Output file path')

    args = parser.parse_args()

    if args.known_only:
        # Just save the comprehensive known courses
        courses = load_known_courses()
    else:
        # Scrape timetable
        subjects = [args.subject.upper()] if args.subject else ['CS', 'MATH', 'STAT', 'PHYS']
        scraped = scrape_timetable(term=args.term, subjects=subjects)

        # Merge with known courses
        known = load_known_courses()
        courses = {**known, **scraped}  # Known takes precedence

    output_path = Path(args.output) if args.output else None
    save_courses(courses, output_path)


if __name__ == '__main__':
    main()
