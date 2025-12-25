"""
VT DARS (Degree Audit Reporting System) Parser
==============================================
Comprehensive parser for Virginia Tech DARS audit reports.
Extracts completed courses, in-progress courses, requirements, and student info.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class GradeType(Enum):
    """Grade types in DARS"""
    LETTER = "letter"      # A, A-, B+, B, etc.
    IN_PROGRESS = "ip"     # IP - currently enrolled
    WITHDRAWN = "withdrawn" # W - withdrawn
    TRANSFER = "transfer"  # TR - transfer credit
    CREDIT_BY_EXAM = "cbe" # CB - credit by exam
    PASS = "pass"          # P - pass/fail
    NO_GRADE = "no_grade"  # NS - no grade (internships)


@dataclass
class Course:
    """Represents a course from DARS"""
    code: str                    # e.g., "CS 1114"
    name: str                    # e.g., "Intro to Software Design"
    credits: float               # e.g., 3.0
    grade: str                   # e.g., "A", "B+", "IP", "W"
    term: str                    # e.g., "24FA" (Fall 2024)
    term_name: str = ""          # e.g., "Fall 2024"
    grade_type: GradeType = GradeType.LETTER
    transfer_from: str = ""      # e.g., "Northern Virginia" for transfer courses
    is_credit_by_exam: bool = False

    def __post_init__(self):
        # Determine grade type
        if self.grade == "IP":
            self.grade_type = GradeType.IN_PROGRESS
        elif self.grade == "W":
            self.grade_type = GradeType.WITHDRAWN
        elif self.grade == "TR":
            self.grade_type = GradeType.TRANSFER
        elif self.grade == "CB":
            self.grade_type = GradeType.CREDIT_BY_EXAM
            self.is_credit_by_exam = True
        elif self.grade in ("P", "S"):
            self.grade_type = GradeType.PASS
        elif self.grade == "NS":
            self.grade_type = GradeType.NO_GRADE

        # Parse term name
        if self.term and len(self.term) >= 4:
            year = "20" + self.term[:2]
            semester = self.term[2:]
            semester_map = {"FA": "Fall", "SP": "Spring", "SU": "Summer", "WI": "Winter"}
            self.term_name = f"{semester_map.get(semester, semester)} {year}"


@dataclass
class Requirement:
    """Represents an unfulfilled requirement"""
    name: str                    # e.g., "Language Study Requirement"
    hours_needed: float          # e.g., 4.0
    courses_needed: int = 0      # e.g., 1
    select_from: List[str] = field(default_factory=list)  # Course options
    description: str = ""


@dataclass
class DARSResult:
    """Complete parsed DARS result"""
    # Student Info
    student_name: str = ""
    student_id: str = ""
    degree: str = ""
    major: str = ""
    minor: Optional[str] = None
    program_code: str = ""
    catalog_year: str = ""
    graduation_date: str = ""
    prepared_date: str = ""

    # GPA Info
    overall_gpa: float = 0.0
    in_major_gpa: float = 0.0

    # Credit Info
    total_credits_earned: float = 0.0
    total_credits_needed: float = 0.0
    vt_credits: float = 0.0
    transfer_credits: float = 0.0

    # Courses
    completed_courses: List[Course] = field(default_factory=list)
    in_progress_courses: List[Course] = field(default_factory=list)
    withdrawn_courses: List[Course] = field(default_factory=list)
    transfer_courses: List[Course] = field(default_factory=list)

    # Requirements
    unfulfilled_requirements: List[Requirement] = field(default_factory=list)

    # Pathways status
    pathways_status: Dict[str, bool] = field(default_factory=dict)


class DARSParser:
    """Parser for VT DARS audit reports"""

    # Regex patterns - handles both "23FA ACIS 1504" and "23FAACIS 1504" formats
    COURSE_PATTERN = re.compile(
        r'(\d{2}[A-Z]{2})\s*'            # Term (e.g., 24FA) - optional space after
        r'([A-Z]{2,4})\s*(\d{4}[A-Z]?)\s+' # Course code split (e.g., ACIS 1504, CS 1114)
        r'(\d+\.?\d*)\s*'                # Credits (e.g., 3.0)
        r'([A-Z][+-]?|IP|W|TR|CB|P|NS)\s+' # Grade
        r'(.+?)(?:\n|$)',                # Course name
        re.MULTILINE
    )

    TERM_PATTERN = re.compile(r'(\d{2})(FA|SP|SU|WI)')

    NEEDS_PATTERN = re.compile(
        r'NEEDS:\s*(\d+\.?\d*)\s*HOURS?(?:\s*(\d+)\s*COURSES?)?',
        re.IGNORECASE
    )

    SELECT_FROM_PATTERN = re.compile(
        r'SELECT FROM:\s*(.+?)(?=\n[A-Z]|\n\n|\Z)',
        re.MULTILINE | re.DOTALL
    )

    GPA_PATTERN = re.compile(r'(\d+\.\d+)\s*GPA')

    def __init__(self):
        self.result = DARSResult()

    def parse(self, text: str) -> DARSResult:
        """Parse DARS text and return structured result"""
        self.result = DARSResult()

        # Clean text
        text = self._clean_text(text)

        # Parse sections
        self._parse_header(text)
        self._parse_credit_summary(text)
        self._parse_gpa(text)
        self._parse_course_history(text)
        self._parse_in_progress(text)
        self._parse_requirements(text)
        self._parse_pathways(text)
        self._parse_minor(text)

        return self.result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text

    def _parse_header(self, text: str):
        """Parse header information"""
        # Student name - look for pattern like "Davuluri, Sai Chaitanya"
        name_match = re.search(r'^([A-Za-z]+,\s*[A-Za-z\s]+?)(?:\n|BACHELOR)', text, re.MULTILINE)
        if name_match:
            self.result.student_name = name_match.group(1).strip()

        # Degree
        degree_match = re.search(r'BACHELOR OF SCIENCE IN ([A-Z\s&]+)', text)
        if degree_match:
            self.result.degree = f"BS in {degree_match.group(1).strip().title()}"

        # Major
        major_match = re.search(r'MAJOR\s*[-–]\s*([A-Z\s&]+?)(?:\n|Prepared)', text)
        if major_match:
            self.result.major = major_match.group(1).strip().title()

        # Program Code
        prog_match = re.search(r'Program\s*Code\s*([A-Z]+)', text)
        if prog_match:
            self.result.program_code = prog_match.group(1)

        # Catalog Year
        catalog_match = re.search(r'Catalog Year\s*(Fall|Spring|Summer)?\s*(\d{4})', text)
        if catalog_match:
            semester = catalog_match.group(1) or ""
            year = catalog_match.group(2)
            self.result.catalog_year = f"{semester} {year}".strip()

        # Student ID
        id_match = re.search(r'Student ID\s*(\d+)', text)
        if id_match:
            self.result.student_id = id_match.group(1)

        # Graduation Date
        grad_match = re.search(r'Graduation\s*Date\s*(\d{1,2}/\d{1,2}/\d{2,4})', text)
        if grad_match:
            self.result.graduation_date = grad_match.group(1)

        # Prepared Date
        prep_match = re.search(r'Prepared On\s*(\d{1,2}/\d{1,2}/\d{4}\s*\d{1,2}:\d{2}\s*[AP]M)', text)
        if prep_match:
            self.result.prepared_date = prep_match.group(1)

    def _parse_credit_summary(self, text: str):
        """Parse credit summary section"""
        # Look for the credit summary table
        summary_match = re.search(
            r'VT\s*:\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
            text
        )
        if summary_match:
            self.result.vt_credits = float(summary_match.group(3))

        transfer_match = re.search(
            r'TRANSFER:\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
            text
        )
        if transfer_match:
            self.result.transfer_credits = float(transfer_match.group(3))

        overall_match = re.search(
            r'OVERALL\s*:\s*(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)',
            text
        )
        if overall_match:
            self.result.total_credits_earned = float(overall_match.group(3))

        # Total credits needed
        needs_match = re.search(r'NEEDS:\s*(\d+\.?\d*)\s*HOURS', text)
        if needs_match:
            self.result.total_credits_needed = float(needs_match.group(1))

    def _parse_gpa(self, text: str):
        """Parse GPA information"""
        # Overall GPA
        overall_gpa_match = re.search(r'Overall GPA Must Be.*?AWARDED:\s*(\d+\.\d+)\s*GPA', text, re.DOTALL)
        if overall_gpa_match:
            self.result.overall_gpa = float(overall_gpa_match.group(1))
        else:
            # Try from credit summary
            gpa_match = re.search(r'OVERALL.*?(\d+\.\d+)\s*$', text, re.MULTILINE)
            if gpa_match:
                self.result.overall_gpa = float(gpa_match.group(1))

        # In-major GPA
        major_gpa_match = re.search(r'In-Major GPA.*?(\d+\.\d+)\s*GPA', text, re.DOTALL)
        if major_gpa_match:
            self.result.in_major_gpa = float(major_gpa_match.group(1))

    def _parse_course_history(self, text: str):
        """Parse course history section"""
        # Find Course History section
        history_start = text.find("Course History")
        if history_start == -1:
            # Try parsing all courses from document
            self._parse_all_courses(text)
            return

        history_text = text[history_start:]

        for match in self.COURSE_PATTERN.finditer(history_text):
            term = match.group(1)
            dept = match.group(2).strip()
            num = match.group(3).strip()
            code = f"{dept} {num}"
            credits = float(match.group(4))
            grade = match.group(5).strip()
            name = match.group(6).strip()

            # Check for transfer info on next line
            transfer_from = ""
            if "Northern Virginia" in name or "Transfer" in name:
                transfer_from = "Northern Virginia CC"

            course = Course(
                code=code,
                name=name.split('\n')[0].strip(),  # Get just first line
                credits=credits,
                grade=grade,
                term=term,
                transfer_from=transfer_from
            )

            # Categorize course
            if course.grade_type == GradeType.IN_PROGRESS:
                self.result.in_progress_courses.append(course)
            elif course.grade_type == GradeType.WITHDRAWN:
                self.result.withdrawn_courses.append(course)
            elif course.grade_type == GradeType.TRANSFER:
                self.result.transfer_courses.append(course)
                self.result.completed_courses.append(course)  # Also add to completed
            else:
                self.result.completed_courses.append(course)

    def _parse_all_courses(self, text: str):
        """Parse courses from entire document (fallback)"""
        for match in self.COURSE_PATTERN.finditer(text):
            term = match.group(1)
            dept = match.group(2).strip()
            num = match.group(3).strip()
            code = f"{dept} {num}"
            credits = float(match.group(4))
            grade = match.group(5).strip()
            name = match.group(6).strip()

            course = Course(
                code=code,
                name=name.split('\n')[0].strip(),
                credits=credits,
                grade=grade,
                term=term
            )

            # Categorize and avoid duplicates
            if course.grade_type == GradeType.IN_PROGRESS:
                if not any(c.code == course.code for c in self.result.in_progress_courses):
                    self.result.in_progress_courses.append(course)
            elif course.grade_type == GradeType.WITHDRAWN:
                if not any(c.code == course.code and c.term == course.term for c in self.result.withdrawn_courses):
                    self.result.withdrawn_courses.append(course)
            elif course.grade_type != GradeType.NO_GRADE:
                if not any(c.code == course.code for c in self.result.completed_courses):
                    self.result.completed_courses.append(course)

    def _parse_in_progress(self, text: str):
        """Parse in-progress courses specifically"""
        # Look for IP courses section
        ip_match = re.search(r'In-Progress Courses Have Been Used.*?(\d+\.?\d*)\s*HOURS ADDED(.*?)(?=\d+\)|AWARDED|$)',
                            text, re.DOTALL)
        if ip_match:
            ip_text = ip_match.group(2)
            for match in self.COURSE_PATTERN.finditer(ip_text):
                term = match.group(1)
                dept = match.group(2).strip()
                num = match.group(3).strip()
                code = f"{dept} {num}"
                credits = float(match.group(4))
                grade = match.group(5).strip()
                name = match.group(6).strip()

                if grade == "IP":
                    course = Course(code=code, name=name, credits=credits, grade=grade, term=term)
                    if not any(c.code == course.code for c in self.result.in_progress_courses):
                        self.result.in_progress_courses.append(course)

    def _parse_requirements(self, text: str):
        """Parse unfulfilled requirements (NEEDS sections)"""
        # Language requirement
        if "Language Study Requirement" in text and "NEEDS:" in text[text.find("Language Study"):text.find("Language Study")+500]:
            lang_section = text[text.find("Language Study Requirement"):text.find("Language Study Requirement")+500]
            needs_match = self.NEEDS_PATTERN.search(lang_section)
            if needs_match:
                req = Requirement(
                    name="Language Study Requirement",
                    hours_needed=float(needs_match.group(1)),
                    description="Complete one full year of language study"
                )
                select_match = self.SELECT_FROM_PATTERN.search(lang_section)
                if select_match:
                    req.select_from = self._parse_course_list(select_match.group(1))
                self.result.unfulfilled_requirements.append(req)

        # Find all NEEDS sections
        needs_sections = re.finditer(
            r'(?:Complete|Required).*?NEEDS:\s*(\d+\.?\d*)\s*HOURS(?:\s*(\d+)\s*COURSES?)?\s*'
            r'(?:SELECT FROM:\s*([^\n]+(?:\n[^\n]+)*))?',
            text, re.MULTILINE
        )

        for match in needs_sections:
            # Try to get requirement name from context
            start = max(0, match.start() - 200)
            context = text[start:match.start()]

            # Find the requirement header
            header_match = re.search(r'([A-Z][A-Za-z\s\-&]+(?:Requirement|Courses?|Elective))', context)
            if header_match:
                name = header_match.group(1).strip()
            else:
                name = "Unknown Requirement"

            hours = float(match.group(1))
            courses = int(match.group(2)) if match.group(2) else 0

            req = Requirement(
                name=name,
                hours_needed=hours,
                courses_needed=courses
            )

            if match.group(3):
                req.select_from = self._parse_course_list(match.group(3))

            # Avoid duplicates
            if not any(r.name == req.name for r in self.result.unfulfilled_requirements):
                self.result.unfulfilled_requirements.append(req)

    def _parse_course_list(self, text: str) -> List[str]:
        """Parse a list of course codes from SELECT FROM text"""
        courses = []
        # Match course codes like CS 1114, MATH 2114, etc.
        course_matches = re.findall(r'([A-Z]{2,4}\s*\d{4}[A-Z]?)', text)
        for c in course_matches:
            code = re.sub(r'([A-Z]+)\s*(\d+)', r'\1 \2', c)
            if code not in courses:
                courses.append(code)
        return courses[:20]  # Limit to prevent huge lists

    def _parse_pathways(self, text: str):
        """Parse Pathways concept completion status"""
        pathways = [
            ("Pathways Concept 1", "Discourse"),
            ("Pathways Concept 2", "Critical Thinking in the Humanities"),
            ("Pathways Concept 3", "Reasoning in the Social Sciences"),
            ("Pathways Concept 4", "Reasoning in the Natural Sciences"),
            ("Pathways Concept 5", "Quantitative and Computational Thinking"),
            ("Pathways Concept 6", "Critique and Practice in Design and the Arts"),
            ("Pathways Concept 7", "Critical Analysis of Equity and Identity in the US"),
        ]

        for concept, name in pathways:
            # Check if completed or has NEEDS
            section_start = text.find(concept)
            if section_start != -1:
                section = text[section_start:section_start+1000]
                if "Completed" in section and "NEEDS:" not in section[:500]:
                    self.result.pathways_status[name] = True
                elif "Suspended" in section:
                    self.result.pathways_status[name] = True  # Suspended = not required
                else:
                    self.result.pathways_status[name] = False

    def _parse_minor(self, text: str):
        """Parse minor information"""
        # Look for "X Minor" section header
        minor_match = re.search(r'([A-Z][A-Za-z\s]+?)\s+Minor\s*\n', text)
        if minor_match:
            minor_name = minor_match.group(1).strip()
            # Clean up any garbage before the actual minor name
            # Look for common minor names
            if "Computer Science" in minor_name:
                self.result.minor = "Computer Science"
            elif "Mathematics" in minor_name:
                self.result.minor = "Mathematics"
            elif "Statistics" in minor_name:
                self.result.minor = "Statistics"
            else:
                # Get last few words which are likely the minor name
                words = minor_name.split()
                if len(words) > 3:
                    self.result.minor = " ".join(words[-3:])
                else:
                    self.result.minor = minor_name


def parse_dars(text: str) -> DARSResult:
    """Convenience function to parse DARS text"""
    parser = DARSParser()
    return parser.parse(text)


def dars_to_dict(result: DARSResult) -> dict:
    """Convert DARSResult to dictionary for JSON serialization"""
    return {
        "student_info": {
            "name": result.student_name,
            "id": result.student_id,
            "degree": result.degree,
            "major": result.major,
            "minor": result.minor,
            "program_code": result.program_code,
            "catalog_year": result.catalog_year,
            "graduation_date": result.graduation_date,
        },
        "gpa": {
            "overall": result.overall_gpa,
            "in_major": result.in_major_gpa,
        },
        "credits": {
            "earned": result.total_credits_earned,
            "needed": result.total_credits_needed,
            "vt": result.vt_credits,
            "transfer": result.transfer_credits,
        },
        "completed_courses": [
            {
                "code": c.code,
                "name": c.name,
                "credits": c.credits,
                "grade": c.grade,
                "term": c.term,
                "term_name": c.term_name,
            }
            for c in result.completed_courses
        ],
        "in_progress_courses": [
            {
                "code": c.code,
                "name": c.name,
                "credits": c.credits,
                "term": c.term,
                "term_name": c.term_name,
            }
            for c in result.in_progress_courses
        ],
        "withdrawn_courses": [
            {
                "code": c.code,
                "name": c.name,
                "term": c.term,
            }
            for c in result.withdrawn_courses
        ],
        "requirements_needed": [
            {
                "name": r.name,
                "hours_needed": r.hours_needed,
                "courses_needed": r.courses_needed,
                "select_from": r.select_from,
            }
            for r in result.unfulfilled_requirements
        ],
        "pathways_status": result.pathways_status,
    }


if __name__ == "__main__":
    # Test with sample text
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            text = f.read()
        result = parse_dars(text)
        import json
        print(json.dumps(dars_to_dict(result), indent=2))
