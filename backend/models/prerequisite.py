"""
Prerequisite Data Model with AND/OR Support
============================================
Supports complex prerequisite structures like:
  - CS 2114 AND (MATH 2534 OR MATH 3034)
  - 12 credits of CS at 3000+ level

The tree structure:
  {"type": "AND", "requirements": [
      {"type": "COURSE", "code": "CS 2114"},
      {"type": "OR", "requirements": [
          {"type": "COURSE", "code": "MATH 2534"},
          {"type": "COURSE", "code": "MATH 3034"}
      ]}
  ]}
"""

from typing import List, Optional, Set


def normalize_code(code: str) -> str:
    """Normalize course code for comparison."""
    return code.upper().replace(" ", "").replace("-", "")


def evaluate_prereqs(prereq_node, completed: Set[str]) -> bool:
    """Evaluate whether prerequisites are satisfied.

    Args:
        prereq_node: A prerequisite tree node (dict) or None.
        completed: Set of normalized course codes the student has completed.

    Returns:
        True if prerequisites are satisfied.
    """
    if prereq_node is None:
        return True

    node_type = prereq_node.get("type")

    if node_type == "COURSE":
        code = normalize_code(prereq_node["code"])
        return code in completed

    if node_type == "AND":
        reqs = prereq_node.get("requirements", [])
        return all(evaluate_prereqs(r, completed) for r in reqs)

    if node_type == "OR":
        reqs = prereq_node.get("requirements", [])
        return any(evaluate_prereqs(r, completed) for r in reqs)

    if node_type == "CREDITS":
        # e.g., {"type": "CREDITS", "min_credits": 12, "department": "CS", "min_level": 3000}
        return _check_credit_requirement(prereq_node, completed)

    # Unknown type - treat as satisfied
    return True


def get_missing_prereqs(prereq_node, completed: Set[str]) -> List[str]:
    """Get list of missing prerequisites (human-readable descriptions).

    Args:
        prereq_node: A prerequisite tree node (dict) or None.
        completed: Set of normalized course codes.

    Returns:
        List of missing prerequisite descriptions.
    """
    if prereq_node is None:
        return []

    node_type = prereq_node.get("type")

    if node_type == "COURSE":
        code = prereq_node["code"]
        if normalize_code(code) not in completed:
            return [code]
        return []

    if node_type == "AND":
        missing = []
        for r in prereq_node.get("requirements", []):
            missing.extend(get_missing_prereqs(r, completed))
        return missing

    if node_type == "OR":
        # Only missing if ALL options are missing
        reqs = prereq_node.get("requirements", [])
        if any(evaluate_prereqs(r, completed) for r in reqs):
            return []
        # All missing - report as "one of X, Y, Z"
        codes = _collect_course_codes(prereq_node)
        if codes:
            return [f"one of: {', '.join(codes)}"]
        return []

    if node_type == "CREDITS":
        if not _check_credit_requirement(prereq_node, completed):
            dept = prereq_node.get("department", "")
            min_credits = prereq_node.get("min_credits", 0)
            min_level = prereq_node.get("min_level", 0)
            return [f"{min_credits} credits of {dept} {min_level}+"]
        return []

    return []


def get_all_prereq_courses(prereq_node) -> List[str]:
    """Extract all course codes referenced in a prerequisite tree.

    Returns flat list of all course codes (for dependency graph building).
    """
    if prereq_node is None:
        return []
    return _collect_course_codes(prereq_node)


def flat_prereqs_to_structured(prereqs: List[str]) -> Optional[dict]:
    """Convert a flat prerequisite list (AND-all) to structured format.

    Args:
        prereqs: List of course codes, all required (AND).

    Returns:
        Structured prerequisite node, or None if empty.
    """
    if not prereqs:
        return None

    if len(prereqs) == 1:
        return {"type": "COURSE", "code": prereqs[0]}

    return {
        "type": "AND",
        "requirements": [{"type": "COURSE", "code": code} for code in prereqs]
    }


# --- Internal helpers ---

def _collect_course_codes(node) -> List[str]:
    """Recursively collect all course codes from a tree."""
    if node is None:
        return []

    node_type = node.get("type")

    if node_type == "COURSE":
        return [node["code"]]

    if node_type in ("AND", "OR"):
        codes = []
        for r in node.get("requirements", []):
            codes.extend(_collect_course_codes(r))
        return codes

    return []


def _check_credit_requirement(node: dict, completed: Set[str]) -> bool:
    """Check a credit-count prerequisite."""
    min_credits = node.get("min_credits", 0)
    department = node.get("department", "").upper()
    min_level = node.get("min_level", 0)

    # This requires access to course credit data, which we don't have here.
    # For now, count matching courses * 3 credits as an approximation.
    count = 0
    for code in completed:
        # De-normalize to check department and level
        parts = code.replace("-", "")
        # Try to extract dept and number
        dept = ""
        num = ""
        for i, ch in enumerate(parts):
            if ch.isdigit():
                dept = parts[:i].strip()
                num = parts[i:].strip()
                break

        if department and dept != department:
            continue
        if min_level and num:
            try:
                if int(num) < min_level:
                    continue
            except ValueError:
                continue
        count += 3  # Approximate 3 credits per course

    return count >= min_credits
