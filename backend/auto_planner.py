"""
Auto Course Planner Engine
============================
Generates optimized semester-by-semester course plans for any VT major.
Uses constraint satisfaction + topological sort with configurable priorities.

Priorities:
  - on_time: Graduate in 4 years, front-load prerequisites
  - maximize_gpa: Easiest path, spread hard courses, avoid overload
  - career_optimized: Align electives with career goals

Usage:
    from auto_planner import AutoPlanner
    planner = AutoPlanner(courses_db, degree_req, offering_patterns)
    result = planner.generate_plan(completed=["CS 1114"], ...)
"""

import json
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
from models.prerequisite import evaluate_prereqs, get_all_prereq_courses, flat_prereqs_to_structured


# Semester IDs in order
SEMESTER_ORDER = [
    "fall1", "spring1", "fall2", "spring2",
    "fall3", "spring3", "fall4", "spring4"
]

SEMESTER_TERMS = {
    "fall1": "Fall", "spring1": "Spring",
    "fall2": "Fall", "spring2": "Spring",
    "fall3": "Fall", "spring3": "Spring",
    "fall4": "Fall", "spring4": "Spring",
}

# Career path course recommendations
CAREER_ELECTIVES = {
    "software_engineering": {
        "recommended": ["CS 3704", "CS 3724", "CS 4704", "CS 4274", "CS 4784"],
        "weight": 5,
    },
    "ai_ml": {
        "recommended": ["CS 4804", "CS 4824", "CS 4644", "STAT 4706", "MATH 4564"],
        "weight": 5,
    },
    "systems": {
        "recommended": ["CS 4114", "CS 4254", "CS 4284", "CS 4264", "ECE 2564"],
        "weight": 5,
    },
    "security": {
        "recommended": ["CS 4264", "CS 4284", "CS 4114", "ECE 4560"],
        "weight": 5,
    },
    "hci": {
        "recommended": ["CS 3724", "CS 3744", "CS 4784", "CS 4234"],
        "weight": 5,
    },
    "data_science": {
        "recommended": ["CS 4804", "CS 4824", "CS 4604", "STAT 4706", "CMDA 3654"],
        "weight": 5,
    },
}


class AutoPlanner:
    def __init__(self, courses_db: dict, degree_req: dict, offering_patterns: dict = None):
        """Initialize planner.

        Args:
            courses_db: All courses dict {code: {name, prereqs, credits, difficulty, ...}}
            degree_req: Degree requirements from degree_requirements_loader
            offering_patterns: Optional {code: ["Fall", "Spring"]} override
        """
        self.courses = courses_db
        self.degree_req = degree_req
        self.offerings = offering_patterns or {}

    def generate_plan(
        self,
        completed: List[str] = None,
        in_progress: List[str] = None,
        start_semester: str = "fall1",
        remaining_semesters: int = 8,
        priority: str = "on_time",
        career_path: str = None,
        preferences: dict = None,
    ) -> dict:
        """Generate an optimized course plan.

        Returns:
            {
                "schedule": {"fall1": ["CS 1114", ...], ...},
                "metadata": {"total_credits": 120, "courses_placed": 40, ...},
                "warnings": ["Could not place CS 4104 - check prerequisites"],
                "unplaced": ["CS 4104"]
            }
        """
        completed = set(completed or [])
        in_progress = set(in_progress or [])
        preferences = preferences or {}

        # Determine active semesters
        start_idx = SEMESTER_ORDER.index(start_semester) if start_semester in SEMESTER_ORDER else 0
        active_semesters = SEMESTER_ORDER[start_idx:start_idx + remaining_semesters]

        # Step 1: Determine what courses are needed
        needed = self._compute_needed_courses(completed, in_progress, career_path, priority)

        # Step 2: Build prerequisite DAG
        dag, all_needed_codes = self._build_prereq_dag(needed, completed | in_progress)

        # Step 3: Topological sort with priority weights
        sorted_courses = self._prioritized_topological_sort(dag, all_needed_codes, needed)

        # Step 4: Schedule into semesters
        max_credits = preferences.get("max_credits", 16 if priority == "maximize_gpa" else 18)
        max_difficulty = preferences.get("max_difficulty_score", 12 if priority == "maximize_gpa" else 16)
        balanced = preferences.get("balanced", priority == "maximize_gpa")

        schedule, unplaced = self._schedule_courses(
            sorted_courses, completed, in_progress,
            active_semesters, max_credits, max_difficulty, balanced
        )

        # Step 5: Optimization pass
        schedule = self._optimize(schedule, priority, career_path, balanced)

        # Build metadata
        total_credits = 0
        courses_placed = 0
        for sem_courses in schedule.values():
            for code in sem_courses:
                total_credits += self._get_credits(code)
                courses_placed += 1

        existing_credits = sum(self._get_credits(c) for c in completed | in_progress)

        warnings = []
        if unplaced:
            warnings.append(f"{len(unplaced)} courses could not be scheduled")
            for code in unplaced[:5]:
                warnings.append(f"  - {code}: check prerequisites or offering patterns")

        total_needed = self.degree_req.get("total_credits", 120)
        if total_credits + existing_credits < total_needed:
            deficit = total_needed - (total_credits + existing_credits)
            warnings.append(f"Plan has {deficit} fewer credits than required ({total_needed})")

        return {
            "schedule": schedule,
            "metadata": {
                "total_credits_planned": total_credits,
                "existing_credits": existing_credits,
                "total_credits": total_credits + existing_credits,
                "credits_required": total_needed,
                "courses_placed": courses_placed,
                "courses_unplaced": len(unplaced),
                "semesters_used": len([s for s in schedule.values() if s]),
                "priority": priority,
                "career_path": career_path,
            },
            "warnings": warnings,
            "unplaced": unplaced,
        }

    def _compute_needed_courses(
        self, completed: Set[str], in_progress: Set[str],
        career_path: str = None, priority: str = "on_time"
    ) -> List[dict]:
        """Determine all courses a student still needs."""
        all_done = self._normalize_set(completed | in_progress)
        needed = []

        # Core courses
        for course in self.degree_req.get("core_courses", []):
            if self._normalize(course) not in all_done:
                needed.append({
                    "code": course,
                    "priority": "REQUIRED",
                    "weight": 100,
                    "reason": "core_requirement"
                })

        # Math requirements
        for course in self.degree_req.get("math_requirements", []):
            if self._normalize(course) not in all_done:
                needed.append({
                    "code": course,
                    "priority": "REQUIRED",
                    "weight": 95,
                    "reason": "math_requirement"
                })

        # Choice requirements - pick best option
        for choice_name, choice_info in self.degree_req.get("choice_requirements", {}).items():
            options = choice_info.get("from", [])
            pick = choice_info.get("pick", 1)
            satisfied = [opt for opt in options if self._normalize(opt) in all_done]

            if len(satisfied) < pick:
                remaining_pick = pick - len(satisfied)
                available_opts = [opt for opt in options if self._normalize(opt) not in all_done]
                selected = self._pick_best_options(available_opts, remaining_pick, career_path, priority)
                for course in selected:
                    needed.append({
                        "code": course,
                        "priority": "REQUIRED",
                        "weight": 90,
                        "reason": f"choice_{choice_name}"
                    })

        # Science requirements
        science_req = self.degree_req.get("science_requirements", {})
        if "sequences" in science_req:
            pick_seq = science_req.get("pick_sequences", 1)
            satisfied_seq = 0
            for seq in science_req["sequences"]:
                if all(self._normalize(c) in all_done for c in seq["courses"]):
                    satisfied_seq += 1
            if satisfied_seq < pick_seq:
                # Pick a sequence - prefer one with partial progress
                best_seq = self._pick_best_sequence(science_req["sequences"], all_done)
                if best_seq:
                    for course in best_seq["courses"]:
                        if self._normalize(course) not in all_done:
                            needed.append({
                                "code": course,
                                "priority": "REQUIRED",
                                "weight": 85,
                                "reason": "science_sequence"
                            })
        if "required" in science_req:
            for seq in science_req["required"]:
                for course in seq["courses"]:
                    if self._normalize(course) not in all_done:
                        needed.append({
                            "code": course,
                            "priority": "REQUIRED",
                            "weight": 85,
                            "reason": "science_required"
                        })

        # Elective requirements
        for cat, req_info in self.degree_req.get("elective_requirements", {}).items():
            min_courses = req_info.get("min_courses", 0)
            filter_str = req_info.get("filter", "")
            current_count = self._count_matching(all_done, filter_str)

            if current_count < min_courses:
                remaining = min_courses - current_count
                options = self._get_elective_options(filter_str, all_done)
                selected = self._pick_best_options(options, remaining, career_path, priority)
                for course in selected:
                    needed.append({
                        "code": course,
                        "priority": "ELECTIVE",
                        "weight": 50,
                        "reason": f"elective_{cat}"
                    })

        # Add pathways/gen-ed placeholders if needed
        pathways_credits = self.degree_req.get("pathways_credits", 0)
        if pathways_credits > 0:
            pathways_done = self._count_pathways(all_done)
            remaining_pathways = (pathways_credits - pathways_done) // 3
            for i in range(max(0, remaining_pathways)):
                needed.append({
                    "code": f"Pathway {i+1}",
                    "priority": "PATHWAY",
                    "weight": 30,
                    "reason": "pathways"
                })

        return needed

    def _build_prereq_dag(
        self, needed: List[dict], already_done: Set[str]
    ) -> Tuple[Dict[str, Set[str]], Set[str]]:
        """Build prerequisite DAG, including transitive prereqs."""
        done_normalized = self._normalize_set(already_done)
        dag = {}
        all_codes = set()
        to_process = [n["code"] for n in needed if not n["code"].startswith("Pathway")]
        processed = set()

        while to_process:
            code = to_process.pop(0)
            if code in processed or self._normalize(code) in done_normalized:
                continue
            processed.add(code)
            all_codes.add(code)

            prereqs = self._get_prereq_courses(code)
            dag[code] = set()
            for prereq in prereqs:
                if self._normalize(prereq) not in done_normalized:
                    dag[code].add(prereq)
                    if prereq not in processed:
                        to_process.append(prereq)

        return dag, all_codes

    def _prioritized_topological_sort(
        self, dag: Dict[str, Set[str]], all_codes: Set[str],
        needed: List[dict]
    ) -> List[dict]:
        """Topological sort with priority weights for scheduling order."""
        # Build weight map from needed list
        weight_map = {}
        reason_map = {}
        for n in needed:
            if n["code"] not in weight_map or n["weight"] > weight_map[n["code"]]:
                weight_map[n["code"]] = n["weight"]
                reason_map[n["code"]] = n.get("reason", "")

        # Add implicit prereqs that aren't in needed but are in the DAG
        for code in all_codes:
            if code not in weight_map:
                weight_map[code] = 80  # Transitive prereqs are important
                reason_map[code] = "transitive_prereq"

        # Kahn's algorithm with priority queue
        in_degree = defaultdict(int)
        for code in all_codes:
            if code not in in_degree:
                in_degree[code] = 0
            for prereq in dag.get(code, set()):
                in_degree[prereq]  # Ensure exists

        for code, prereqs in dag.items():
            for prereq in prereqs:
                in_degree[code] += 1  # This is wrong direction, let me fix

        # Rebuild in_degree correctly
        in_degree = defaultdict(int)
        for code in all_codes:
            in_degree[code] = 0
        for code, prereqs in dag.items():
            in_degree[code] = len(prereqs)

        # Start with courses that have no unmet prereqs
        ready = []
        for code in all_codes:
            if in_degree[code] == 0:
                ready.append(code)

        # Sort ready by weight (highest first)
        ready.sort(key=lambda c: -weight_map.get(c, 0))

        result = []
        placed = set()

        while ready:
            # Pick highest priority course
            code = ready.pop(0)
            if code in placed:
                continue
            placed.add(code)

            result.append({
                "code": code,
                "weight": weight_map.get(code, 0),
                "reason": reason_map.get(code, ""),
            })

            # Update in-degrees
            for other_code in all_codes:
                if code in dag.get(other_code, set()):
                    in_degree[other_code] -= 1
                    if in_degree[other_code] <= 0 and other_code not in placed:
                        ready.append(other_code)

            ready.sort(key=lambda c: -weight_map.get(c, 0))

        # Add pathway placeholders at the end
        for n in needed:
            if n["code"].startswith("Pathway"):
                result.append(n)

        return result

    def _schedule_courses(
        self, sorted_courses: List[dict], completed: Set[str],
        in_progress: Set[str], active_semesters: List[str],
        max_credits: int, max_difficulty: int, balanced: bool
    ) -> Tuple[Dict[str, List[str]], List[str]]:
        """Place courses into semester slots respecting constraints."""
        schedule = {sem: [] for sem in active_semesters}
        placed = self._normalize_set(completed | in_progress)
        placed_codes = set(completed | in_progress)
        unplaced = []

        for course_info in sorted_courses:
            code = course_info["code"]
            if self._normalize(code) in placed:
                continue

            # Try each semester in order
            course_placed = False
            for sem_id in active_semesters:
                if self._can_place(code, sem_id, schedule, placed_codes,
                                   max_credits, max_difficulty, balanced):
                    schedule[sem_id].append(code)
                    placed.add(self._normalize(code))
                    placed_codes.add(code)
                    course_placed = True
                    break

            if not course_placed:
                unplaced.append(code)

        return schedule, unplaced

    def _can_place(
        self, code: str, sem_id: str, schedule: dict,
        placed_codes: Set[str], max_credits: int,
        max_difficulty: int, balanced: bool
    ) -> bool:
        """Check if a course can be placed in a given semester."""
        # Skip pathway placeholders - they can go anywhere
        if code.startswith("Pathway"):
            # Check credit limit
            current_credits = sum(self._get_credits(c) for c in schedule[sem_id])
            return current_credits + 3 <= max_credits

        # Check course offering pattern
        term = SEMESTER_TERMS.get(sem_id, "Fall")
        offered = self._get_offerings(code)
        if offered and term not in offered:
            return False

        # Check prerequisites are satisfied BEFORE this semester
        # Build set of only courses completed or placed in EARLIER semesters
        sem_idx = SEMESTER_ORDER.index(sem_id) if sem_id in SEMESTER_ORDER else 0
        available_before = set(placed_codes)
        # Remove courses placed in current or later semesters
        for later_sem in SEMESTER_ORDER[sem_idx:]:
            if later_sem in schedule:
                for c in schedule[later_sem]:
                    available_before.discard(c)

        prereqs = self._get_prereq_courses(code)
        for prereq in prereqs:
            if self._normalize(prereq) not in self._normalize_set(available_before):
                return False

        # Check credit limit
        current_credits = sum(self._get_credits(c) for c in schedule[sem_id])
        course_credits = self._get_credits(code)
        if current_credits + course_credits > max_credits:
            return False

        # Check difficulty balance
        current_difficulty = sum(self._get_difficulty(c) for c in schedule[sem_id])
        course_difficulty = self._get_difficulty(code)
        if current_difficulty + course_difficulty > max_difficulty:
            return False

        # Check max hard courses (difficulty >= 4)
        if balanced and course_difficulty >= 4:
            hard_count = sum(1 for c in schedule[sem_id] if self._get_difficulty(c) >= 4)
            if hard_count >= 2:
                return False

        return True

    def _optimize(
        self, schedule: dict, priority: str,
        career_path: str = None, balanced: bool = False
    ) -> dict:
        """Post-processing optimization pass."""
        if priority == "maximize_gpa":
            schedule = self._balance_difficulty(schedule)
        elif priority == "on_time":
            schedule = self._front_load_prereqs(schedule)
        return schedule

    def _balance_difficulty(self, schedule: dict) -> dict:
        """Spread hard courses more evenly across semesters."""
        # Find semesters with multiple hard courses
        for sem_id, courses in schedule.items():
            hard = [c for c in courses if self._get_difficulty(c) >= 4]
            if len(hard) <= 2:
                continue

            # Try to move extra hard courses to adjacent semesters
            sem_idx = SEMESTER_ORDER.index(sem_id) if sem_id in SEMESTER_ORDER else -1
            for excess_course in hard[2:]:
                # Try next semesters
                for offset in [1, -1, 2, -2]:
                    target_idx = sem_idx + offset
                    if 0 <= target_idx < len(SEMESTER_ORDER):
                        target_sem = SEMESTER_ORDER[target_idx]
                        if target_sem in schedule:
                            target_hard = sum(1 for c in schedule[target_sem]
                                              if self._get_difficulty(c) >= 4)
                            target_credits = sum(self._get_credits(c)
                                                 for c in schedule[target_sem])
                            if target_hard < 2 and target_credits + self._get_credits(excess_course) <= 18:
                                schedule[sem_id].remove(excess_course)
                                schedule[target_sem].append(excess_course)
                                break
        return schedule

    def _front_load_prereqs(self, schedule: dict) -> dict:
        """Ensure prerequisite chains are scheduled as early as possible."""
        # Already handled by topological sort - this is a no-op for now
        return schedule

    # --- Helper methods ---

    def _normalize(self, code: str) -> str:
        return code.upper().replace(" ", "").replace("-", "")

    def _normalize_set(self, codes) -> Set[str]:
        return {self._normalize(c) for c in codes}

    def _get_credits(self, code: str) -> int:
        if code.startswith("Pathway"):
            return 3
        info = self.courses.get(code, {})
        return info.get("credits", 3)

    def _get_difficulty(self, code: str) -> int:
        if code.startswith("Pathway"):
            return 1
        # Check degree requirement difficulty ratings first
        ratings = self.degree_req.get("difficulty_ratings", {})
        if code in ratings:
            return ratings[code]
        # Then check course database
        info = self.courses.get(code, {})
        return info.get("difficulty", 3)

    def _get_offerings(self, code: str) -> List[str]:
        """Get when a course is typically offered."""
        if code in self.offerings:
            return self.offerings[code]
        info = self.courses.get(code, {})
        return info.get("typically_offered", [])

    def _get_prereq_courses(self, code: str) -> List[str]:
        """Get flat list of prerequisite course codes."""
        info = self.courses.get(code, {})

        # Try structured prereqs first
        structured = info.get("prereqs_structured")
        if structured:
            return get_all_prereq_courses(structured)

        # Fall back to flat list
        return info.get("prereqs", [])

    def _pick_best_options(
        self, options: List[str], pick: int,
        career_path: str = None, priority: str = "on_time"
    ) -> List[str]:
        """Pick the best N courses from a list of options."""
        if not options:
            return []

        scored = []
        for code in options:
            score = 0
            info = self.courses.get(code, {})

            # Career alignment bonus
            if career_path and career_path in CAREER_ELECTIVES:
                if code in CAREER_ELECTIVES[career_path]["recommended"]:
                    score += 20

            # Difficulty preference
            difficulty = self._get_difficulty(code)
            if priority == "maximize_gpa":
                score -= difficulty * 3  # Prefer easier courses
            elif priority == "on_time":
                score += 5  # Neutral

            # Prefer courses with fewer prereqs (easier to schedule)
            prereqs = len(info.get("prereqs", []))
            score -= prereqs * 2

            scored.append((score, code))

        scored.sort(key=lambda x: -x[0])
        return [code for _, code in scored[:pick]]

    def _pick_best_sequence(self, sequences: list, done_normalized: Set[str]) -> dict:
        """Pick the science sequence with most partial progress."""
        best = None
        best_progress = -1

        for seq in sequences:
            progress = sum(1 for c in seq["courses"] if self._normalize(c) in done_normalized)
            if progress > best_progress:
                best_progress = progress
                best = seq

        return best or (sequences[0] if sequences else None)

    def _count_matching(self, done_normalized: Set[str], filter_str: str) -> int:
        """Count courses matching a filter like 'CS 3000+'."""
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

        stem_depts = {"CS", "ECE", "ME", "MATH", "STAT", "PHYS", "CHEM", "BIOL",
                      "CMDA", "AOE", "BSE", "CEE", "CHE", "ESM", "ISE", "MSE"}

        count = 0
        for code in done_normalized:
            dept = ""
            num_str = ""
            for i, ch in enumerate(code):
                if ch.isdigit():
                    dept = code[:i]
                    num_str = code[i:]
                    break
            if not dept:
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

    def _get_elective_options(self, filter_str: str, done_normalized: Set[str]) -> List[str]:
        """Get available elective courses matching a filter."""
        if not filter_str:
            return []

        parts = filter_str.split()
        if len(parts) != 2:
            return []

        dept_filter = parts[0].upper()
        level_str = parts[1].replace("+", "")
        try:
            min_level = int(level_str)
        except ValueError:
            return []

        stem_depts = {"CS", "ECE", "ME", "MATH", "STAT", "PHYS", "CHEM", "BIOL",
                      "CMDA", "AOE", "BSE", "CEE", "CHE", "ESM", "ISE", "MSE"}

        options = []
        for code in self.courses:
            norm = self._normalize(code)
            if norm in done_normalized:
                continue

            parts_code = code.split()
            if len(parts_code) != 2:
                continue

            dept = parts_code[0]
            try:
                num = int(parts_code[1])
            except ValueError:
                continue

            if dept_filter == "STEM":
                if dept in stem_depts and num >= min_level:
                    options.append(code)
            elif dept == dept_filter and num >= min_level:
                options.append(code)

        return options[:50]  # Limit to prevent explosion

    def _count_pathways(self, done_normalized: Set[str]) -> int:
        """Estimate pathways credits completed."""
        pathway_depts = {"ENGL", "COMM", "PHIL", "ECON", "PSYC", "SOC", "HIST",
                         "PSCI", "ART", "MUS", "HUM", "RLCL", "WGS"}
        count = 0
        for code in done_normalized:
            dept = ""
            for i, ch in enumerate(code):
                if ch.isdigit():
                    dept = code[:i]
                    break
            if dept in pathway_depts:
                count += 3
        return count
