"""
VT CS AI Academic Advisor
Comprehensive AI service with VT-specific rules, course data, and degree requirements
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# VT CS DEGREE REQUIREMENTS (Hardcoded Rules)
# ============================================================================

class DegreeRequirement:
    """VT CS BS Degree Requirements - 120 credits total"""

    # Core CS courses (MUST complete all)
    CS_CORE = ["CS 1114", "CS 2114", "CS 2505", "CS 2506", "CS 3114", "CS 3214"]

    # Theory requirement
    CS_THEORY = ["CS 4104"]  # Required

    # Systems elective (choose 1)
    CS_SYSTEMS_OPTIONS = ["CS 4114", "CS 4254", "CS 4284"]

    # Capstone options (choose 1)
    CAPSTONE_OPTIONS = ["CS 4704", "CS 4784", "CS 4884", "CS 4274", "CS 4664", "CS 4094"]

    # Math requirements
    MATH_CORE = ["MATH 1225", "MATH 1226", "MATH 2114"]
    DISCRETE_MATH = ["MATH 2534", "MATH 3034"]  # Choose 1

    # Stats requirement (choose 1)
    STATS_OPTIONS = ["STAT 4705", "STAT 4714", "STAT 3005", "STAT 3104"]

    # Science requirements (2 sequences, typically Physics)
    SCIENCE_SEQUENCES = {
        "physics": ["PHYS 2305", "PHYS 2306"],
        "chemistry": ["CHEM 1035", "CHEM 1036"],
        "biology": ["BIOL 1105", "BIOL 1106"]
    }

    # CS Electives requirement (minimum 3 courses, 9 credits)
    MIN_CS_ELECTIVES = 3

    # Total credit requirements
    TOTAL_CREDITS = 120
    CS_CREDITS_MIN = 45

    # Pathways/Gen Ed requirements
    PATHWAY_CREDITS = 18  # 6 courses


# ============================================================================
# COURSE SEQUENCING RULES (Hardcoded Prerequisites)
# ============================================================================

PREREQUISITE_RULES = {
    # CS Core sequence
    "CS 2114": {"prereqs": ["CS 1114"], "min_grade": "C"},
    "CS 2505": {"prereqs": ["CS 2114", "MATH 2534"], "min_grade": "C"},
    "CS 2506": {"prereqs": ["CS 2505", "CS 2114"], "min_grade": "C"},
    "CS 3114": {"prereqs": ["CS 2114", "CS 2505"], "min_grade": "C"},
    "CS 3214": {"prereqs": ["CS 2506", "CS 3114"], "min_grade": "C"},

    # Theory & upper level
    "CS 4104": {"prereqs": ["CS 3114", "MATH 2534"], "min_grade": "C"},
    "CS 4114": {"prereqs": ["CS 3114", "MATH 2534"], "min_grade": "C"},
    "CS 4124": {"prereqs": ["CS 4114"], "min_grade": "C"},
    "CS 4254": {"prereqs": ["CS 3214"], "min_grade": "C"},
    "CS 4264": {"prereqs": ["CS 3214"], "min_grade": "C"},
    "CS 4284": {"prereqs": ["CS 3214"], "min_grade": "C"},

    # Electives
    "CS 3304": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 3604": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 3704": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 3714": {"prereqs": ["CS 2114"], "min_grade": "C"},
    "CS 3724": {"prereqs": ["CS 2114"], "min_grade": "C"},
    "CS 3744": {"prereqs": ["CS 2114"], "min_grade": "C"},
    "CS 3824": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 4204": {"prereqs": ["CS 3114", "CS 3744"], "min_grade": "C"},
    "CS 4234": {"prereqs": ["CS 3214"], "min_grade": "C"},
    "CS 4304": {"prereqs": ["CS 3114", "CS 3214"], "min_grade": "C"},
    "CS 4604": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 4704": {"prereqs": ["CS 3704"], "min_grade": "C"},
    "CS 4784": {"prereqs": ["CS 3724", "CS 3744"], "min_grade": "C"},
    "CS 4804": {"prereqs": ["CS 3114"], "min_grade": "C"},
    "CS 4824": {"prereqs": ["CS 3114", "STAT 4714"], "min_grade": "C"},
    "CS 4884": {"prereqs": ["CS 3824"], "min_grade": "C"},

    # Math sequence
    "MATH 1226": {"prereqs": ["MATH 1225"], "min_grade": "C"},
    "MATH 2114": {"prereqs": ["MATH 1226"], "min_grade": "C"},
    "MATH 2534": {"prereqs": ["MATH 1225"], "min_grade": "C"},

    # Physics
    "PHYS 2305": {"prereqs": ["MATH 1225"], "min_grade": "C"},
    "PHYS 2306": {"prereqs": ["PHYS 2305", "MATH 1226"], "min_grade": "C"},
}


# ============================================================================
# COURSE DIFFICULTY & WORKLOAD DATA
# ============================================================================

COURSE_DIFFICULTY = {
    # Hardest courses (5/5)
    "CS 3214": {"difficulty": 5, "workload": 5, "notes": "Notoriously difficult, heavy C programming"},

    # Very challenging (4/5)
    "CS 3114": {"difficulty": 4, "workload": 4, "notes": "Data structures, algorithm analysis"},
    "CS 4104": {"difficulty": 4, "workload": 3, "notes": "Theory-heavy, proofs required"},
    "CS 2506": {"difficulty": 4, "workload": 4, "notes": "Assembly, hardware concepts"},
    "CS 4114": {"difficulty": 4, "workload": 3, "notes": "Automata theory, formal proofs"},
    "CS 4304": {"difficulty": 4, "workload": 4, "notes": "Compiler construction"},

    # Moderately challenging (3/5)
    "CS 2114": {"difficulty": 3, "workload": 3, "notes": "OOP, data structures intro"},
    "CS 2505": {"difficulty": 3, "workload": 3, "notes": "C programming, memory"},
    "CS 4254": {"difficulty": 3, "workload": 3, "notes": "Networking concepts"},
    "CS 4264": {"difficulty": 3, "workload": 3, "notes": "Security fundamentals"},
    "CS 4604": {"difficulty": 3, "workload": 3, "notes": "Database design, SQL"},
    "CS 4804": {"difficulty": 3, "workload": 3, "notes": "AI fundamentals"},
    "CS 4824": {"difficulty": 3, "workload": 4, "notes": "ML algorithms, math-heavy"},

    # Standard difficulty (2/5)
    "CS 1114": {"difficulty": 2, "workload": 2, "notes": "Intro course, Python"},
    "CS 3604": {"difficulty": 2, "workload": 2, "notes": "Ethics, professional topics"},
    "CS 3704": {"difficulty": 2, "workload": 3, "notes": "Software engineering"},
    "CS 3724": {"difficulty": 2, "workload": 2, "notes": "HCI concepts"},
}

# Maximum recommended difficulty points per semester
MAX_DIFFICULTY_PER_SEMESTER = 12  # e.g., max 2 hard courses + 2 medium


# ============================================================================
# CAREER PATH RECOMMENDATIONS
# ============================================================================

CAREER_PATHS = {
    "software_engineering": {
        "name": "Software Engineering",
        "recommended": ["CS 3704", "CS 4704", "CS 3714", "CS 4604"],
        "description": "Full-stack development, software design patterns"
    },
    "systems": {
        "name": "Systems & Infrastructure",
        "recommended": ["CS 4254", "CS 4284", "CS 4264", "CS 4234"],
        "description": "Operating systems, networks, security"
    },
    "ai_ml": {
        "name": "AI & Machine Learning",
        "recommended": ["CS 4804", "CS 4824", "CS 3654", "CS 4654"],
        "description": "Artificial intelligence, data science"
    },
    "hci": {
        "name": "Human-Computer Interaction",
        "recommended": ["CS 3724", "CS 3744", "CS 4784", "CS 4644"],
        "description": "UX design, interactive systems"
    },
    "theory": {
        "name": "Theory & Research",
        "recommended": ["CS 4104", "CS 4114", "CS 4124", "CS 3304"],
        "description": "Academic research, algorithm design"
    },
    "security": {
        "name": "Cybersecurity",
        "recommended": ["CS 4264", "CS 4274", "CS 3214", "CS 4254"],
        "description": "Security analysis, penetration testing"
    }
}


# ============================================================================
# SEMESTER RULES & CONSTRAINTS
# ============================================================================

SEMESTER_RULES = {
    "max_credits": 18,
    "min_credits": 12,
    "max_hard_courses": 2,  # Courses with difficulty >= 4
    "recommended_credits": 15,
    "warning_credits": 17,

    # Course availability (some courses only offered certain semesters)
    "fall_only": ["CS 4704"],
    "spring_only": ["CS 4784"],

    # Recommended sequences by year
    "year_1": {
        "fall": ["CS 1114", "MATH 1225", "ENGL 1105"],
        "spring": ["CS 2114", "MATH 1226", "PHYS 2305"]
    },
    "year_2": {
        "fall": ["CS 2505", "CS 2506", "MATH 2114", "MATH 2534"],
        "spring": ["CS 3114", "PHYS 2306", "STAT 4714"]
    },
    "year_3": {
        "fall": ["CS 3214", "CS 4104", "CS elective"],
        "spring": ["CS systems elective", "CS electives"]
    },
    "year_4": {
        "fall": ["CS electives", "Capstone prep"],
        "spring": ["Capstone", "CS electives"]
    }
}


# ============================================================================
# AI ADVISOR CLASS
# ============================================================================

class VTAdvisor:
    """AI Academic Advisor for VT CS students"""

    def __init__(self):
        self.courses = self._load_courses()
        self.gemini_client = None
        self.gemini_model = None
        self._init_gemini()

    def _load_courses(self) -> Dict:
        """Load course data from JSON file"""
        courses_file = Path(__file__).parent / "data" / "courses.json"
        try:
            with open(courses_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _init_gemini(self):
        """Initialize Gemini AI client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=api_key)
                self.gemini_model = "gemini-2.0-flash-lite"
            except Exception as e:
                print(f"Gemini init failed: {e}")
                self.gemini_client = None

    def _build_context(self) -> str:
        """Build comprehensive context for AI with all rules and data"""
        context = """
# VIRGINIA TECH COMPUTER SCIENCE DEGREE REQUIREMENTS

## Core Requirements (MUST complete all):
- CS Core: CS 1114 → CS 2114 → CS 2505 → CS 2506 → CS 3114 → CS 3214
- Theory: CS 4104 (Data & Algorithm Analysis)
- Systems Elective: Choose 1 from CS 4114, CS 4254, or CS 4284
- Capstone: Choose 1 from CS 4704, CS 4784, CS 4884, CS 4274, CS 4664

## Math Requirements:
- Calculus: MATH 1225 → MATH 1226
- Linear Algebra: MATH 2114
- Discrete Math: MATH 2534 or MATH 3034

## Statistics (choose 1):
- STAT 4705, STAT 4714, STAT 3005, or STAT 3104

## Science (2-course sequence):
- Physics: PHYS 2305 → PHYS 2306 (recommended for CS)
- OR Chemistry: CHEM 1035 → CHEM 1036
- OR Biology: BIOL 1105 → BIOL 1106

## CS Electives:
- Minimum 3 courses (9 credits) from 3000/4000 level CS courses

## STRICT RULES:
1. Prerequisites MUST be completed BEFORE taking a course (not same semester)
2. Maximum 18 credits per semester
3. Minimum C grade required in all CS/Math prerequisites
4. CS 3214 should NOT be taken with other hard courses (CS 3114, CS 4104)
5. CS 4104 requires both CS 3114 AND MATH 2534

## DIFFICULTY RATINGS:
- CS 3214: 5/5 (HARDEST - take alone if possible)
- CS 3114, CS 4104, CS 2506, CS 4114: 4/5 (Very challenging)
- CS 2114, CS 2505, CS 4604, CS 4804: 3/5 (Moderate)
- CS 1114, CS 3604, CS 3704: 2/5 (Manageable)

## RECOMMENDED SEQUENCES:
Year 1 Fall: CS 1114, MATH 1225
Year 1 Spring: CS 2114, MATH 1226, PHYS 2305
Year 2 Fall: CS 2505, MATH 2534, MATH 2114
Year 2 Spring: CS 2506, CS 3114, STAT 4714
Year 3 Fall: CS 3214 (ALONE or with easy courses)
Year 3 Spring: CS 4104, Systems elective
Year 4: Capstone + electives

## COMMON MISTAKES TO WARN ABOUT:
1. Taking CS 3214 with CS 3114 or CS 4104 (too hard)
2. Taking CS 2506 before CS 2505
3. Forgetting MATH 2534 (needed for CS 2505, CS 4104)
4. Overloading with hard courses
5. Not planning capstone prerequisites early enough
"""
        return context

    def check_prerequisites(self, course: str, completed: set, semester_courses: set) -> Tuple[bool, List[str]]:
        """Check if prerequisites are met for a course"""
        if course not in PREREQUISITE_RULES:
            return True, []

        rules = PREREQUISITE_RULES[course]
        missing = []

        for prereq in rules["prereqs"]:
            # Prereq must be in completed, NOT in same semester
            if prereq not in completed:
                missing.append(prereq)

        return len(missing) == 0, missing

    def calculate_semester_difficulty(self, courses: List[str]) -> int:
        """Calculate total difficulty score for a semester"""
        total = 0
        for course in courses:
            if course in COURSE_DIFFICULTY:
                total += COURSE_DIFFICULTY[course]["difficulty"]
            else:
                total += 3  # Default difficulty
        return total

    def check_degree_progress(self, completed: List[str], planned: Dict[str, List[str]]) -> Dict:
        """Check progress toward degree completion"""
        all_planned = set()
        for courses in planned.values():
            all_planned.update(courses)

        all_courses = set(completed) | all_planned

        progress = {
            "cs_core": {
                "required": DegreeRequirement.CS_CORE,
                "completed": [c for c in DegreeRequirement.CS_CORE if c in completed],
                "planned": [c for c in DegreeRequirement.CS_CORE if c in all_planned and c not in completed],
                "missing": [c for c in DegreeRequirement.CS_CORE if c not in all_courses]
            },
            "theory": {
                "required": DegreeRequirement.CS_THEORY,
                "completed": [c for c in DegreeRequirement.CS_THEORY if c in completed],
                "planned": [c for c in DegreeRequirement.CS_THEORY if c in all_planned],
                "missing": [c for c in DegreeRequirement.CS_THEORY if c not in all_courses]
            },
            "systems_elective": {
                "options": DegreeRequirement.CS_SYSTEMS_OPTIONS,
                "satisfied": any(c in all_courses for c in DegreeRequirement.CS_SYSTEMS_OPTIONS),
                "chosen": [c for c in DegreeRequirement.CS_SYSTEMS_OPTIONS if c in all_courses]
            },
            "capstone": {
                "options": DegreeRequirement.CAPSTONE_OPTIONS,
                "satisfied": any(c in all_courses for c in DegreeRequirement.CAPSTONE_OPTIONS),
                "chosen": [c for c in DegreeRequirement.CAPSTONE_OPTIONS if c in all_courses]
            },
            "math_core": {
                "required": DegreeRequirement.MATH_CORE,
                "completed": [c for c in DegreeRequirement.MATH_CORE if c in completed],
                "missing": [c for c in DegreeRequirement.MATH_CORE if c not in all_courses]
            },
            "discrete_math": {
                "options": DegreeRequirement.DISCRETE_MATH,
                "satisfied": any(c in all_courses for c in DegreeRequirement.DISCRETE_MATH),
            },
            "stats": {
                "options": DegreeRequirement.STATS_OPTIONS,
                "satisfied": any(c in all_courses for c in DegreeRequirement.STATS_OPTIONS),
            }
        }

        return progress

    def suggest_courses(self, completed: List[str], current_plan: Dict[str, List[str]],
                       career_interest: str = None) -> List[Dict]:
        """Generate smart course suggestions"""
        suggestions = []
        completed_set = set(completed)
        all_planned = set()
        for courses in current_plan.values():
            all_planned.update(courses)

        all_courses = completed_set | all_planned

        # Check degree progress
        progress = self.check_degree_progress(completed, current_plan)

        # Priority 1: Missing core requirements
        for core in progress["cs_core"]["missing"]:
            # Check if prereqs are met
            can_take, missing_prereqs = self.check_prerequisites(core, completed_set, set())
            suggestions.append({
                "course": core,
                "priority": "HIGH",
                "reason": "Required CS core course",
                "prereqs_met": can_take,
                "missing_prereqs": missing_prereqs
            })

        # Priority 2: Theory requirement
        if not progress["theory"]["completed"] and not progress["theory"]["planned"]:
            suggestions.append({
                "course": "CS 4104",
                "priority": "HIGH",
                "reason": "Required theory course for graduation",
                "prereqs_met": "CS 3114" in all_courses and "MATH 2534" in all_courses,
                "missing_prereqs": [p for p in ["CS 3114", "MATH 2534"] if p not in all_courses]
            })

        # Priority 3: Systems elective
        if not progress["systems_elective"]["satisfied"]:
            for option in DegreeRequirement.CS_SYSTEMS_OPTIONS:
                can_take, missing = self.check_prerequisites(option, completed_set, set())
                suggestions.append({
                    "course": option,
                    "priority": "MEDIUM",
                    "reason": f"Systems elective option - {self.courses.get(option, {}).get('name', option)}",
                    "prereqs_met": can_take,
                    "missing_prereqs": missing
                })

        # Priority 4: Capstone
        if not progress["capstone"]["satisfied"]:
            for option in DegreeRequirement.CAPSTONE_OPTIONS:
                can_take, missing = self.check_prerequisites(option, completed_set, set())
                if option in self.courses:
                    suggestions.append({
                        "course": option,
                        "priority": "MEDIUM",
                        "reason": f"Capstone option - {self.courses.get(option, {}).get('name', option)}",
                        "prereqs_met": can_take,
                        "missing_prereqs": missing
                    })

        # Priority 5: Career-aligned electives
        if career_interest and career_interest in CAREER_PATHS:
            path = CAREER_PATHS[career_interest]
            for course in path["recommended"]:
                if course not in all_courses and course in self.courses:
                    can_take, missing = self.check_prerequisites(course, completed_set, set())
                    suggestions.append({
                        "course": course,
                        "priority": "LOW",
                        "reason": f"Recommended for {path['name']} career path",
                        "prereqs_met": can_take,
                        "missing_prereqs": missing
                    })

        return suggestions

    async def analyze_plan(self, plan: Dict[str, List[str]], completed: List[str],
                          in_progress: List[str] = [], major: str = "CS", minor: str = None) -> Dict:
        """Comprehensive AI-powered plan analysis for any major/minor"""
        # Import degree requirements for the specified major
        try:
            from degree_requirements import get_requirements, check_graduation_progress, SUPPORTED_MINORS
            major_req = get_requirements(major)
            major_name = major_req.major_name if major_req else "Computer Science"
            # Get minor name if provided
            minor_name = None
            if minor:
                minor_info = next((m for m in SUPPORTED_MINORS if m["code"] == minor), None)
                minor_name = minor_info["name"] if minor_info else minor
        except:
            major_name = "Computer Science"
            major_req = None
            minor_name = minor

        # Rule-based analysis first
        issues = []
        warnings = []
        suggestions = []
        positives = []

        semester_order = ["fall1", "spring1", "fall2", "spring2", "fall3", "spring3", "fall4", "spring4"]
        taken_before = set(completed + in_progress)

        total_planned_credits = 0
        hard_course_semesters = []

        for sem in semester_order:
            courses = plan.get(sem, [])
            if not courses:
                continue

            sem_credits = sum(self.courses.get(c, {}).get("credits", 3) for c in courses)
            total_planned_credits += sem_credits

            sem_name = sem.replace("fall", "Fall Y").replace("spring", "Spring Y")

            # Check prerequisites
            for course in courses:
                can_take, missing = self.check_prerequisites(course, taken_before, set(courses))
                if not can_take:
                    issues.append(f"{sem_name}: {course} missing prerequisites: {', '.join(missing)}")

            # Check credit load
            if sem_credits > 18:
                issues.append(f"{sem_name}: {sem_credits} credits exceeds maximum 18")
            elif sem_credits > 16:
                warnings.append(f"{sem_name}: Heavy load ({sem_credits} credits)")

            # Check difficulty
            difficulty = self.calculate_semester_difficulty(courses)
            hard_courses = [c for c in courses if COURSE_DIFFICULTY.get(c, {}).get("difficulty", 3) >= 4]

            if len(hard_courses) > 2:
                issues.append(f"{sem_name}: Too many hard courses: {', '.join(hard_courses)}")
            elif len(hard_courses) == 2:
                warnings.append(f"{sem_name}: Two challenging courses together: {', '.join(hard_courses)}")

            # CS 3214 special check
            if "CS 3214" in courses:
                other_hard = [c for c in courses if c != "CS 3214" and COURSE_DIFFICULTY.get(c, {}).get("difficulty", 3) >= 4]
                if other_hard:
                    issues.append(f"{sem_name}: CS 3214 should not be taken with {', '.join(other_hard)}")
                if sem_credits > 15:
                    warnings.append(f"{sem_name}: Consider lighter load when taking CS 3214")

            taken_before.update(courses)

        # Check degree progress
        progress = self.check_degree_progress(completed, plan)

        if progress["cs_core"]["missing"]:
            issues.append(f"Missing required CS core: {', '.join(progress['cs_core']['missing'])}")

        if not progress["theory"]["completed"] and not progress["theory"]["planned"]:
            warnings.append("CS 4104 (Theory) not yet planned - required for graduation")

        if not progress["systems_elective"]["satisfied"]:
            warnings.append("No systems elective planned (need CS 4114, 4254, or 4284)")

        if not progress["capstone"]["satisfied"]:
            warnings.append("No capstone course planned")

        if not progress["discrete_math"]["satisfied"]:
            issues.append("MATH 2534 or MATH 3034 required but not planned")

        # Positives
        if "CS 3114" in taken_before:
            positives.append("Data Structures (CS 3114) completed - unlocks many electives")
        if "CS 3214" in taken_before:
            positives.append("Computer Systems (CS 3214) completed - major milestone!")
        if progress["cs_core"]["completed"]:
            positives.append(f"{len(progress['cs_core']['completed'])}/6 CS core courses completed")
        if not issues:
            positives.append("No prerequisite violations detected!")

        # Calculate score
        base_score = 100
        base_score -= len(issues) * 15
        base_score -= len(warnings) * 5
        base_score = max(0, min(100, base_score))

        # Get AI-enhanced analysis if available
        ai_suggestions = []
        if self.gemini_client:
            try:
                ai_response = await self._get_ai_suggestions(plan, completed, issues, warnings, major_name, minor_name)
                if ai_response:
                    ai_suggestions = ai_response.get("suggestions", [])
                    # Merge AI positives
                    ai_positives = ai_response.get("positives", [])
                    positives.extend([p for p in ai_positives if p not in positives])
            except Exception as e:
                print(f"AI suggestions failed: {e}")

        # Get rule-based suggestions
        course_suggestions = self.suggest_courses(completed, plan)

        return {
            "overallScore": base_score,
            "issues": issues,
            "warnings": warnings,
            "suggestions": ai_suggestions or [s["reason"] for s in course_suggestions[:5]],
            "positives": positives,
            "degreeProgress": progress,
            "courseSuggestions": course_suggestions[:10],
            "careerPaths": CAREER_PATHS
        }

    async def _get_ai_suggestions(self, plan: Dict, completed: List[str],
                                  issues: List[str], warnings: List[str],
                                  major_name: str = "Computer Science", minor_name: str = None) -> Dict:
        """Get AI-enhanced suggestions from Gemini"""
        if not self.gemini_client:
            return {}

        context = self._build_context()

        plan_summary = []
        for sem_id, courses in plan.items():
            if courses:
                sem_name = sem_id.replace("fall", "Fall Y").replace("spring", "Spring Y")
                plan_summary.append(f"{sem_name}: {', '.join(courses)}")

        # Build student info with major/minor
        student_info = f"Major: {major_name}"
        if minor_name:
            student_info += f"\nMinor: {minor_name}"

        prompt = f"""{context}

## STUDENT'S CURRENT SITUATION:

{student_info}

Completed courses: {', '.join(completed) if completed else 'None'}

Planned semesters:
{chr(10).join(plan_summary) if plan_summary else 'No courses planned yet'}

Already identified issues: {'; '.join(issues) if issues else 'None'}
Already identified warnings: {'; '.join(warnings) if warnings else 'None'}

## YOUR TASK:
Provide personalized advice for this VT {major_name} student{' with a ' + minor_name + ' minor' if minor_name else ''}. Return JSON:
{{
    "suggestions": ["Specific actionable suggestion 1", "Suggestion 2", "Suggestion 3"],
    "positives": ["Positive observation 1", "Positive observation 2"],
    "careerAlignment": "Which career path their electives suggest",
    "semesterTip": "Specific tip for their next semester"
}}

Focus on:
1. What they should take next based on their progress and major/minor requirements
2. Career-relevant elective recommendations that complement their major{' and ' + minor_name + ' minor' if minor_name else ''}
3. Workload balancing tips
4. Any opportunities they might be missing
5. {'Courses that would fulfill both major and minor requirements' if minor_name else 'Potential minors that complement their major'}"""

        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3
                }
            )
            return json.loads(response.text)
        except:
            return {}

    async def simulate_addition(self, course: str, semester: str,
                               current_plan: Dict, completed: List[str]) -> Dict:
        """Simulate adding a course and return impact analysis"""
        # Create modified plan
        new_plan = {k: list(v) for k, v in current_plan.items()}
        if semester not in new_plan:
            new_plan[semester] = []
        new_plan[semester].append(course)

        # Analyze both
        current_analysis = await self.analyze_plan(current_plan, completed)
        new_analysis = await self.analyze_plan(new_plan, completed)

        return {
            "course": course,
            "semester": semester,
            "scoreBefore": current_analysis["overallScore"],
            "scoreAfter": new_analysis["overallScore"],
            "scoreChange": new_analysis["overallScore"] - current_analysis["overallScore"],
            "newIssues": [i for i in new_analysis["issues"] if i not in current_analysis["issues"]],
            "newWarnings": [w for w in new_analysis["warnings"] if w not in current_analysis["warnings"]],
            "recommendation": "GOOD" if new_analysis["overallScore"] >= current_analysis["overallScore"] else "CAUTION"
        }


# Singleton instance
advisor = VTAdvisor()
