#!/usr/bin/env python3
"""
Enhanced Prerequisite Parser
===============================
Re-parses prerequisite text from catalog descriptions into AND/OR tree structures.
Uses regex for common patterns and Gemini AI for complex cases.

Usage:
    python enhance_prerequisites.py              # Process all courses
    python enhance_prerequisites.py --subject CS  # Process specific subject
    python enhance_prerequisites.py --test        # Test with sample prereq strings
"""

import asyncio
import json
import re
import os
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

COURSES_FILE = Path(__file__).parent.parent / "data" / "courses.json"

# Regex pattern for course codes
COURSE_PATTERN = re.compile(r'([A-Z]{2,4})\s*(\d{4})')


def parse_prereq_text(text: str) -> dict:
    """Parse a prerequisite text string into a structured AND/OR tree.

    Examples:
        "CS 2114" -> {"type": "COURSE", "code": "CS 2114"}
        "CS 2114 and MATH 2534" -> {"type": "AND", ...}
        "MATH 2534 or MATH 3034" -> {"type": "OR", ...}
        "CS 2114 and (MATH 2534 or MATH 3034)" -> nested AND/OR
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # Remove common prefixes
    text = re.sub(r'^(?:pre-?requisite\(?s?\)?:?\s*)', '', text, flags=re.I)

    # Extract all course codes
    codes = COURSE_PATTERN.findall(text)
    if not codes:
        return None

    unique_codes = list(dict.fromkeys(f"{d} {n}" for d, n in codes))

    if len(unique_codes) == 1:
        return {"type": "COURSE", "code": unique_codes[0]}

    # Determine the connective structure
    text_lower = text.lower()

    # Check for explicit parenthetical grouping: "X and (Y or Z)"
    paren_result = _parse_with_parentheses(text)
    if paren_result:
        return paren_result

    # Simple "or" only (no "and")
    if ' or ' in text_lower and ' and ' not in text_lower:
        return {
            "type": "OR",
            "requirements": [{"type": "COURSE", "code": c} for c in unique_codes]
        }

    # Simple "and" only (no "or")
    if ' and ' in text_lower and ' or ' not in text_lower:
        return {
            "type": "AND",
            "requirements": [{"type": "COURSE", "code": c} for c in unique_codes]
        }

    # Mixed "and" + "or" without parentheses
    # Try to parse clause by clause
    if ' and ' in text_lower and ' or ' in text_lower:
        return _parse_mixed(text, unique_codes)

    # Comma-separated (treat as AND by default)
    if ',' in text:
        return {
            "type": "AND",
            "requirements": [{"type": "COURSE", "code": c} for c in unique_codes]
        }

    # Multiple codes with no clear connective - treat as AND
    return {
        "type": "AND",
        "requirements": [{"type": "COURSE", "code": c} for c in unique_codes]
    }


def _parse_with_parentheses(text: str) -> dict:
    """Handle explicit parenthetical groups like 'CS 2114 and (MATH 2534 or MATH 3034)'."""
    # Find parenthetical groups
    paren_groups = re.finditer(r'\(([^)]+)\)', text)
    groups = [(m.start(), m.end(), m.group(1)) for m in paren_groups]

    if not groups:
        return None

    # Split the text around parenthetical groups
    parts = []
    last_end = 0

    for start, end, group_text in groups:
        # Text before the group
        before = text[last_end:start].strip()
        if before:
            parts.append(("text", before))
        # The group itself
        parts.append(("group", group_text))
        last_end = end

    # Text after last group
    remaining = text[last_end:].strip()
    if remaining:
        parts.append(("text", remaining))

    # Build the tree
    requirements = []
    for part_type, part_text in parts:
        if part_type == "group":
            # Parse the group content
            group_codes = COURSE_PATTERN.findall(part_text)
            group_unique = list(dict.fromkeys(f"{d} {n}" for d, n in group_codes))

            if not group_unique:
                continue

            if len(group_unique) == 1:
                requirements.append({"type": "COURSE", "code": group_unique[0]})
            elif ' or ' in part_text.lower():
                requirements.append({
                    "type": "OR",
                    "requirements": [{"type": "COURSE", "code": c} for c in group_unique]
                })
            else:
                requirements.append({
                    "type": "AND",
                    "requirements": [{"type": "COURSE", "code": c} for c in group_unique]
                })
        else:
            # Extract individual course codes from non-group text
            text_codes = COURSE_PATTERN.findall(part_text)
            for d, n in text_codes:
                code = f"{d} {n}"
                requirements.append({"type": "COURSE", "code": code})

    if not requirements:
        return None
    if len(requirements) == 1:
        return requirements[0]

    # Determine top-level connective from the original text
    text_lower = text.lower()
    # Remove parenthetical content to check top-level connective
    clean = re.sub(r'\([^)]+\)', '', text_lower)
    if ' or ' in clean and ' and ' not in clean:
        return {"type": "OR", "requirements": requirements}

    return {"type": "AND", "requirements": requirements}


def _parse_mixed(text: str, codes: list) -> dict:
    """Parse text with mixed AND/OR like 'CS 2114 and MATH 2534 or MATH 3034'.

    Heuristic: group consecutive OR'd courses together.
    'A and B or C' -> AND(A, OR(B, C))
    'A or B and C or D' -> AND(OR(A, B), OR(C, D))
    """
    text_lower = text.lower()

    # Split by 'and' first
    and_parts = re.split(r'\s+and\s+', text_lower)

    requirements = []
    for part in and_parts:
        # Check if this part has OR
        if ' or ' in part:
            or_codes = COURSE_PATTERN.findall(part.upper())
            or_unique = list(dict.fromkeys(f"{d} {n}" for d, n in or_codes))
            if len(or_unique) > 1:
                requirements.append({
                    "type": "OR",
                    "requirements": [{"type": "COURSE", "code": c} for c in or_unique]
                })
            elif or_unique:
                requirements.append({"type": "COURSE", "code": or_unique[0]})
        else:
            part_codes = COURSE_PATTERN.findall(part.upper())
            for d, n in part_codes:
                requirements.append({"type": "COURSE", "code": f"{d} {n}"})

    if not requirements:
        return {"type": "AND", "requirements": [{"type": "COURSE", "code": c} for c in codes]}
    if len(requirements) == 1:
        return requirements[0]
    return {"type": "AND", "requirements": requirements}


async def process_courses_with_gemini(courses: dict, subject_filter: str = None):
    """Use Gemini to parse complex prerequisite texts."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠ GEMINI_API_KEY not set, skipping AI enhancement")
        return

    from google import genai
    client = genai.Client(api_key=api_key)

    # Find courses with complex prereq text that our regex might miss
    complex_courses = []
    for code, info in courses.items():
        if subject_filter and not code.startswith(subject_filter + " "):
            continue
        desc = info.get("description", "")
        prereq_match = re.search(r'prerequisite\(?s?\)?:?\s*(.+?)(?:\.|$)', desc, re.I)
        if prereq_match:
            prereq_text = prereq_match.group(1)
            # Check if it's complex (mixed AND/OR with parentheses)
            if ('(' in prereq_text and ' or ' in prereq_text.lower()) or \
               (' and ' in prereq_text.lower() and ' or ' in prereq_text.lower()):
                complex_courses.append((code, prereq_text))

    if not complex_courses:
        return

    print(f"Processing {len(complex_courses)} complex prerequisite texts with Gemini...")

    batch_size = 10
    for i in range(0, len(complex_courses), batch_size):
        batch = complex_courses[i:i+batch_size]

        prompt = """Parse each prerequisite text into an AND/OR tree structure.
Return a JSON array where each element has "code" and "prereqs_structured".

Format for prereqs_structured:
- Single course: {"type": "COURSE", "code": "CS 2114"}
- AND: {"type": "AND", "requirements": [...]}
- OR: {"type": "OR", "requirements": [...]}

Prerequisite texts to parse:
"""
        for code, prereq_text in batch:
            prompt += f'\n{code}: "{prereq_text}"'

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )
            results = json.loads(response.text)

            for result in results:
                course_code = result.get("code", "")
                structured = result.get("prereqs_structured")
                if course_code in courses and structured:
                    courses[course_code]["prereqs_structured"] = structured

        except Exception as e:
            print(f"  Gemini batch failed: {str(e)[:60]}")

        await asyncio.sleep(0.5)


def main():
    parser = argparse.ArgumentParser(description='Enhance prerequisite data')
    parser.add_argument('--subject', type=str, help='Process specific subject')
    parser.add_argument('--test', action='store_true', help='Test with sample texts')
    args = parser.parse_args()

    if args.test:
        # Test with sample prerequisite strings
        test_cases = [
            "CS 2114",
            "CS 2114 and MATH 2534",
            "MATH 2534 or MATH 3034",
            "CS 2114 and (MATH 2534 or MATH 3034)",
            "CS 2506, CS 3114",
            "CS 2114 and CS 2505 and MATH 2114",
            "PHYS 2305 or PHYS 2306 or CHEM 1035",
            "ESM 2104 and ESM 2204 and (MATH 2214 or MATH 2406)",
        ]
        for text in test_cases:
            result = parse_prereq_text(text)
            print(f"  '{text}'")
            print(f"  -> {json.dumps(result, indent=2)}")
            print()
        return

    # Load courses
    if not COURSES_FILE.exists():
        print("courses.json not found!")
        return

    with open(COURSES_FILE) as f:
        data = json.load(f)
    courses = data.get("courses", data)

    print(f"Processing {len(courses)} courses...")

    updated = 0
    subject_filter = args.subject.upper() if args.subject else None

    for code, info in courses.items():
        if subject_filter and not code.startswith(subject_filter + " "):
            continue

        prereqs = info.get("prereqs", [])
        if not prereqs:
            continue

        # Skip if already has structured data
        if "prereqs_structured" in info:
            continue

        # Convert flat list to structured
        if len(prereqs) == 1:
            info["prereqs_structured"] = {"type": "COURSE", "code": prereqs[0]}
        else:
            info["prereqs_structured"] = {
                "type": "AND",
                "requirements": [{"type": "COURSE", "code": p} for p in prereqs]
            }
        updated += 1

    # Save
    if isinstance(data, dict) and "courses" in data:
        data["courses"] = courses
    else:
        data = courses

    with open(COURSES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Added prereqs_structured to {updated} courses")

    # Optionally run Gemini enhancement
    if os.getenv("GEMINI_API_KEY"):
        asyncio.run(process_courses_with_gemini(courses, subject_filter))
        with open(COURSES_FILE, 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    main()
