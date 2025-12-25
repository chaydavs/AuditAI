#!/usr/bin/env python3
"""
VT Course Scraper - Scrapes course data from Coursicle for Virginia Tech
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, List, Optional

# Departments to scrape
DEPARTMENTS = [
    "CS",      # Computer Science
    "MATH",    # Mathematics
    "STAT",    # Statistics
    "PHYS",    # Physics
    "CHEM",    # Chemistry
    "BIOL",    # Biology
    "ENGL",    # English (for pathways)
    "COMM",    # Communication
    "PHIL",    # Philosophy
    "ECON",    # Economics
]

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Course category mapping
def get_category(dept: str, course_num: int, course_name: str) -> str:
    """Determine course category based on department and number"""
    name_lower = course_name.lower()

    if dept == "CS":
        # Core CS courses
        if course_num in [1114, 2114, 2505, 2506, 3114, 3214]:
            return "cs_core"
        # Theory
        if course_num == 4104:
            return "cs_theory"
        # Systems electives
        if course_num in [4114, 4254, 4284]:
            return "cs_systems"
        # Capstone
        if course_num in [4704, 4784, 4884, 4274, 4664]:
            return "capstone"
        # CS electives (3000+ level)
        if course_num >= 3000:
            return "cs_elective"
        return "cs_intro"

    elif dept == "MATH":
        if course_num in [1225, 1226]:
            return "math_core"
        if course_num == 2114:
            return "math_core"
        if course_num in [2534, 3034]:
            return "math_discrete"
        return "math_elective"

    elif dept == "STAT":
        if course_num in [4705, 4714]:
            return "stats"
        return "stats_elective"

    elif dept in ["PHYS", "CHEM", "BIOL"]:
        return "science"

    elif dept in ["ENGL", "COMM", "PHIL", "ECON"]:
        return "pathways"

    return "elective"


def parse_prerequisites(prereq_text: str) -> List[str]:
    """Parse prerequisite text into list of course codes"""
    if not prereq_text or prereq_text.lower() in ["none", "none listed", "—"]:
        return []

    # Find all course patterns like "CS 2114" or "MATH 1226"
    pattern = r'([A-Z]{2,4})\s*(\d{4})'
    matches = re.findall(pattern, prereq_text.upper())

    prereqs = []
    for dept, num in matches:
        prereqs.append(f"{dept} {num}")

    return list(set(prereqs))  # Remove duplicates


def parse_credits(credit_text: str) -> int:
    """Parse credit text into integer"""
    if not credit_text or credit_text == "—":
        return 3  # Default

    # Extract first number
    match = re.search(r'(\d+)', credit_text)
    if match:
        return int(match.group(1))
    return 3


def scrape_coursicle(dept: str) -> List[Dict]:
    """Scrape courses for a department from Coursicle"""
    url = f"https://www.coursicle.com/vt/courses/{dept}/"
    print(f"Scraping {dept} from {url}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {dept}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    courses = []

    # Find course rows - Coursicle uses specific class patterns
    # Look for course links or course containers
    course_links = soup.find_all('a', href=re.compile(f'/vt/courses/{dept}/'))

    seen = set()
    for link in course_links:
        href = link.get('href', '')
        # Extract course number from href like /vt/courses/CS/1114/
        match = re.search(rf'/vt/courses/{dept}/(\d+)/', href)
        if not match:
            continue

        course_num = match.group(1)
        course_code = f"{dept} {course_num}"

        if course_code in seen:
            continue
        seen.add(course_code)

        # Get course name from link text or parent
        course_name = link.get_text(strip=True)
        # Clean up the name - remove course code if it's in the text
        course_name = re.sub(rf'^{dept}\s*{course_num}\s*[-:.]?\s*', '', course_name)

        if not course_name or course_name == course_code:
            course_name = "Course"

        courses.append({
            "code": course_code,
            "dept": dept,
            "number": int(course_num),
            "name": course_name[:100],  # Truncate long names
        })

    print(f"  Found {len(courses)} courses for {dept}")
    return courses


def scrape_course_details(course_code: str) -> Dict:
    """Scrape detailed info for a specific course"""
    dept, num = course_code.split()
    url = f"https://www.coursicle.com/vt/courses/{dept}/{num}/"

    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {}
    except:
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    details = {}

    # Try to find credits
    text = soup.get_text()
    credit_match = re.search(r'(\d+)\s*(?:credit|Credit|cr\.)', text)
    if credit_match:
        details['credits'] = int(credit_match.group(1))

    # Try to find prerequisites
    prereq_match = re.search(r'(?:Prerequisite|Prerequisites?|Pre-req)[s:]?\s*([^.]+)', text, re.IGNORECASE)
    if prereq_match:
        details['prereq_text'] = prereq_match.group(1).strip()
        details['prereqs'] = parse_prerequisites(prereq_match.group(1))

    # Try to find description
    desc_elem = soup.find('div', class_=re.compile('description|desc', re.I))
    if desc_elem:
        details['description'] = desc_elem.get_text(strip=True)[:500]

    return details


def get_known_courses() -> Dict[str, Dict]:
    """Return hardcoded data for key courses we know about"""
    return {
        # CS Core
        "CS 1114": {"name": "Introduction to Software Design", "credits": 3, "prereqs": [], "category": "cs_core"},
        "CS 2114": {"name": "Software Design and Data Structures", "credits": 3, "prereqs": ["CS 1114"], "category": "cs_core"},
        "CS 2505": {"name": "Introduction to Computer Organization", "credits": 3, "prereqs": ["CS 1114", "MATH 2534"], "category": "cs_core"},
        "CS 2506": {"name": "Computer Organization II", "credits": 3, "prereqs": ["CS 2505", "CS 2114"], "category": "cs_core"},
        "CS 3114": {"name": "Data Structures and Algorithms", "credits": 3, "prereqs": ["CS 2114", "CS 2505"], "category": "cs_core"},
        "CS 3214": {"name": "Computer Systems", "credits": 3, "prereqs": ["CS 2506", "CS 3114"], "category": "cs_core"},

        # Theory & Systems
        "CS 4104": {"name": "Data and Algorithm Analysis", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_theory"},
        "CS 4114": {"name": "Formal Languages and Automata", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_systems"},
        "CS 4254": {"name": "Computer Network Architecture", "credits": 3, "prereqs": ["CS 3214"], "category": "cs_systems"},
        "CS 4284": {"name": "Systems and Networking Capstone", "credits": 3, "prereqs": ["CS 3214"], "category": "cs_systems"},

        # CS Electives
        "CS 3304": {"name": "Comparative Languages", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_elective"},
        "CS 3604": {"name": "Professionalism in Computing", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_elective"},
        "CS 3704": {"name": "Intermediate Software Design", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_elective"},
        "CS 3714": {"name": "Mobile Software Development", "credits": 3, "prereqs": ["CS 2114"], "category": "cs_elective"},
        "CS 3724": {"name": "Human-Computer Interaction", "credits": 3, "prereqs": ["CS 2114"], "category": "cs_elective"},
        "CS 3744": {"name": "GUI Programming and Graphics", "credits": 3, "prereqs": ["CS 2114"], "category": "cs_elective"},
        "CS 4604": {"name": "Introduction to Database Management", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_elective"},
        "CS 4804": {"name": "Introduction to Artificial Intelligence", "credits": 3, "prereqs": ["CS 3114"], "category": "cs_elective"},
        "CS 4824": {"name": "Machine Learning", "credits": 3, "prereqs": ["CS 3114", "STAT 4714"], "category": "cs_elective"},
        "CS 4264": {"name": "Principles of Computer Security", "credits": 3, "prereqs": ["CS 3214"], "category": "cs_elective"},
        "CS 4234": {"name": "Parallel Computation", "credits": 3, "prereqs": ["CS 3214"], "category": "cs_elective"},

        # Capstone
        "CS 4704": {"name": "Software Engineering Capstone", "credits": 3, "prereqs": ["CS 3704"], "category": "capstone"},
        "CS 4784": {"name": "HCI Capstone", "credits": 3, "prereqs": ["CS 3724", "CS 3744"], "category": "capstone"},

        # Math Core
        "MATH 1225": {"name": "Calculus of a Single Variable", "credits": 4, "prereqs": [], "category": "math_core"},
        "MATH 1226": {"name": "Calculus of a Single Variable II", "credits": 4, "prereqs": ["MATH 1225"], "category": "math_core"},
        "MATH 2114": {"name": "Linear Algebra", "credits": 3, "prereqs": ["MATH 1226"], "category": "math_core"},
        "MATH 2534": {"name": "Discrete Mathematics", "credits": 3, "prereqs": ["MATH 1225"], "category": "math_discrete"},
        "MATH 3034": {"name": "Discrete Mathematics", "credits": 3, "prereqs": ["MATH 1225"], "category": "math_discrete"},

        # Stats
        "STAT 4705": {"name": "Statistics for Engineers", "credits": 3, "prereqs": ["MATH 1226"], "category": "stats"},
        "STAT 4714": {"name": "Probability and Statistics", "credits": 3, "prereqs": ["MATH 1226"], "category": "stats"},

        # Science
        "PHYS 2305": {"name": "Foundations of Physics I", "credits": 4, "prereqs": ["MATH 1225"], "category": "science"},
        "PHYS 2306": {"name": "Foundations of Physics II", "credits": 4, "prereqs": ["PHYS 2305", "MATH 1226"], "category": "science"},
        "CHEM 1035": {"name": "General Chemistry", "credits": 4, "prereqs": [], "category": "science"},
        "CHEM 1036": {"name": "General Chemistry II", "credits": 4, "prereqs": ["CHEM 1035"], "category": "science"},
        "BIOL 1105": {"name": "Principles of Biology", "credits": 4, "prereqs": [], "category": "science"},
        "BIOL 1106": {"name": "Principles of Biology II", "credits": 4, "prereqs": ["BIOL 1105"], "category": "science"},

        # Intro CS alternatives
        "CS 1044": {"name": "Introduction to Programming in C", "credits": 3, "prereqs": [], "category": "cs_intro"},
        "CS 1054": {"name": "Introduction to Programming in Java", "credits": 3, "prereqs": [], "category": "cs_intro"},
        "CS 1064": {"name": "Introduction to Programming in Python", "credits": 3, "prereqs": [], "category": "cs_intro"},

        # Common pathways
        "ENGL 1105": {"name": "First-Year Writing", "credits": 3, "prereqs": [], "category": "pathways"},
        "ENGL 1106": {"name": "First-Year Writing", "credits": 3, "prereqs": ["ENGL 1105"], "category": "pathways"},
        "COMM 1015": {"name": "Public Speaking", "credits": 3, "prereqs": [], "category": "pathways"},
        "PHIL 1304": {"name": "Ethics and the Social Contract", "credits": 3, "prereqs": [], "category": "pathways"},
        "ECON 2005": {"name": "Principles of Economics", "credits": 3, "prereqs": [], "category": "pathways"},
    }


def merge_course_data(scraped: List[Dict], known: Dict[str, Dict]) -> Dict[str, Dict]:
    """Merge scraped data with known data, preferring known data for key courses"""
    all_courses = {}

    # First add all scraped courses
    for course in scraped:
        code = course['code']
        num = course['number']
        dept = course['dept']

        all_courses[code] = {
            "name": course.get('name', 'Course'),
            "credits": course.get('credits', 3),
            "prereqs": course.get('prereqs', []),
            "category": get_category(dept, num, course.get('name', '')),
        }

    # Override with known data (more accurate)
    for code, data in known.items():
        all_courses[code] = data

    return all_courses


def main():
    print("=" * 60)
    print("VT Course Scraper")
    print("=" * 60)

    all_scraped = []

    # Scrape each department
    for dept in DEPARTMENTS:
        courses = scrape_coursicle(dept)
        all_scraped.extend(courses)
        time.sleep(1)  # Be nice to the server

    print(f"\nTotal scraped: {len(all_scraped)} courses")

    # Get known/verified course data
    known_courses = get_known_courses()
    print(f"Known courses: {len(known_courses)}")

    # Merge data
    final_courses = merge_course_data(all_scraped, known_courses)
    print(f"Final dataset: {len(final_courses)} courses")

    # Save to JSON
    output_file = "courses_data.json"
    with open(output_file, 'w') as f:
        json.dump(final_courses, f, indent=2, sort_keys=True)

    print(f"\nSaved to {output_file}")

    # Print summary by category
    categories = {}
    for code, data in final_courses.items():
        cat = data.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print("\nCourses by category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    return final_courses


if __name__ == "__main__":
    main()
