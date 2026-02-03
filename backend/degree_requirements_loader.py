"""
Degree Requirements Loader
===========================
Loads degree requirements from JSON file instead of hardcoded Python.
Supports all majors, minors, and concentrations.
Falls back to the legacy Python-defined requirements if JSON not available.
"""

import json
from pathlib import Path
from typing import Optional, Dict, List

REQUIREMENTS_FILE = Path(__file__).parent / "data" / "degree_requirements.json"
_cache = None


def load_all_requirements() -> Dict:
    """Load all degree requirements from JSON file (cached)."""
    global _cache
    if _cache is None:
        try:
            with open(REQUIREMENTS_FILE, 'r') as f:
                _cache = json.load(f)
            print(f"✓ Loaded degree requirements for {len(_cache.get('programs', {}))} programs")
        except FileNotFoundError:
            print("⚠ degree_requirements.json not found, using empty defaults")
            _cache = {"programs": {}, "minors": {}, "metadata": {}}
        except json.JSONDecodeError as e:
            print(f"⚠ Error parsing degree_requirements.json: {e}")
            _cache = {"programs": {}, "minors": {}, "metadata": {}}
    return _cache


def reload_requirements():
    """Force reload from disk (after scraper updates the file)."""
    global _cache
    _cache = None
    return load_all_requirements()


def load_requirements(major_code: str, concentration: str = None) -> Optional[Dict]:
    """Load degree requirements for a specific major.

    Args:
        major_code: Major code (e.g., "CS", "ECE", "ME")
        concentration: Optional concentration code (e.g., "CS-AI")

    Returns:
        Dict with all requirement data, or None if not found.
    """
    data = load_all_requirements()
    program = data.get("programs", {}).get(major_code.upper())

    if not program:
        return None

    # Make a copy so we don't mutate cache
    result = json.loads(json.dumps(program))

    # If concentration specified, merge concentration-specific overrides
    if concentration and "concentrations" in result:
        conc = result["concentrations"].get(concentration)
        if conc:
            # Merge additional core courses
            if "additional_core" in conc:
                result["core_courses"] = list(set(result["core_courses"] + conc["additional_core"]))
            # Merge additional elective requirements
            if "additional_electives" in conc:
                result["elective_requirements"].update(conc["additional_electives"])
            # Override recommended sequence if concentration has one
            if "recommended_sequence" in conc:
                result["recommended_sequence"] = conc["recommended_sequence"]

    return result


def load_minor_requirements(minor_code: str) -> Optional[Dict]:
    """Load requirements for a specific minor."""
    data = load_all_requirements()
    return data.get("minors", {}).get(minor_code.upper())


def list_available_programs() -> List[Dict]:
    """List all programs that have full requirements defined."""
    data = load_all_requirements()
    programs = []
    for code, info in data.get("programs", {}).items():
        programs.append({
            "code": code,
            "name": info.get("major_name", ""),
            "college": info.get("college", ""),
            "degree": info.get("degree", "BS"),
            "has_concentrations": bool(info.get("concentrations")),
            "has_sequence": bool(info.get("recommended_sequence")),
        })
    return sorted(programs, key=lambda x: x["code"])


def list_available_minors() -> List[Dict]:
    """List all minors that have requirements defined."""
    data = load_all_requirements()
    minors = []
    for code, info in data.get("minors", {}).items():
        minors.append({
            "code": code,
            "name": info.get("minor_name", ""),
            "total_credits": info.get("total_credits", 0),
        })
    return sorted(minors, key=lambda x: x["code"])


def get_needed_courses(major_code: str, completed: List[str],
                       concentration: str = None,
                       minor_code: str = None) -> Dict:
    """Determine what courses a student still needs for graduation.

    Returns:
        Dict with keys: required, choices, electives, math, science, pathways
        Each contains remaining courses/requirements.
    """
    req = load_requirements(major_code, concentration)
    if not req:
        return {"error": f"No requirements found for {major_code}"}

    completed_set = set(c.upper().replace(" ", "").replace("-", "") for c in completed)

    def normalize(code):
        return code.upper().replace(" ", "").replace("-", "")

    result = {
        "required": [],
        "choices": {},
        "electives": {},
        "math": [],
        "science": {},
        "minor": [],
    }

    # Core courses still needed
    for course in req.get("core_courses", []):
        if normalize(course) not in completed_set:
            result["required"].append(course)

    # Choice requirements
    for choice_name, choice_info in req.get("choice_requirements", {}).items():
        options = choice_info.get("from", [])
        pick = choice_info.get("pick", 1)
        satisfied = [opt for opt in options if normalize(opt) in completed_set]
        if len(satisfied) < pick:
            result["choices"][choice_name] = {
                "pick": pick - len(satisfied),
                "from": [opt for opt in options if normalize(opt) not in completed_set],
                "satisfied": satisfied,
            }

    # Elective requirements
    for cat, req_info in req.get("elective_requirements", {}).items():
        min_courses = req_info.get("min_courses", 0)
        filter_str = req_info.get("filter", "")
        # Count how many matching courses have been completed
        count = _count_matching_courses(completed_set, filter_str)
        if count < min_courses:
            result["electives"][cat] = {
                "need": min_courses - count,
                "have": count,
                "filter": filter_str,
            }

    # Math still needed
    for course in req.get("math_requirements", []):
        if normalize(course) not in completed_set:
            result["math"].append(course)

    # Science still needed
    science_req = req.get("science_requirements", {})
    if "sequences" in science_req:
        pick = science_req.get("pick_sequences", 1)
        satisfied_sequences = 0
        for seq in science_req["sequences"]:
            if all(normalize(c) in completed_set for c in seq["courses"]):
                satisfied_sequences += 1
        if satisfied_sequences < pick:
            result["science"]["sequences_needed"] = pick - satisfied_sequences
            result["science"]["options"] = science_req["sequences"]
    if "required" in science_req:
        for seq in science_req["required"]:
            missing = [c for c in seq["courses"] if normalize(c) not in completed_set]
            if missing:
                result["science"][seq["name"]] = missing

    # Minor requirements
    if minor_code:
        minor_req = load_minor_requirements(minor_code)
        if minor_req:
            for course in minor_req.get("required_courses", []):
                if normalize(course) not in completed_set:
                    result["minor"].append(course)

    return result


def _count_matching_courses(completed_set: set, filter_str: str) -> int:
    """Count completed courses matching a filter like 'CS 3000+' or 'STEM 2000+'."""
    if not filter_str:
        return 0

    parts = filter_str.split()
    if len(parts) != 2:
        return 0

    dept_filter = parts[0].upper()
    level_str = parts[1].replace("+", "")

    try:
        min_level = int(level_str)
    except ValueError:
        return 0

    # STEM means any engineering/science department
    stem_depts = {"CS", "ECE", "ME", "MATH", "STAT", "PHYS", "CHEM", "BIOL",
                  "CMDA", "AOE", "BSE", "CEE", "CHE", "ESM", "ISE", "MSE",
                  "MINE", "NSEG", "BMES"}

    count = 0
    for code in completed_set:
        # Parse department and number from normalized code
        dept = ""
        num_str = ""
        for i, ch in enumerate(code):
            if ch.isdigit():
                dept = code[:i]
                num_str = code[i:]
                break

        if not dept or not num_str:
            continue

        try:
            num = int(num_str)
        except ValueError:
            continue

        if dept_filter == "STEM":
            if dept in stem_depts and num >= min_level:
                count += 1
        elif dept == dept_filter and num >= min_level:
            count += 1

    return count
