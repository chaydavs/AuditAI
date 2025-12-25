"""
VT Degree Requirements by Major
===============================
Comprehensive degree requirements for various Virginia Tech majors.
Requirements sourced from VT Academic Catalog.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class DegreeRequirement:
    """Requirements for a specific degree program"""
    major_code: str
    major_name: str
    college: str
    total_credits: int = 120

    # Core courses required for the major
    core_courses: List[str] = field(default_factory=list)

    # Courses where student must pick one/some from options
    choice_requirements: Dict[str, List[str]] = field(default_factory=dict)

    # Minimum number of electives needed from specific categories
    elective_requirements: Dict[str, int] = field(default_factory=dict)

    # Math requirements
    math_requirements: List[str] = field(default_factory=list)

    # Science requirements
    science_requirements: Dict[str, List[str]] = field(default_factory=dict)

    # Pathways/General education
    pathways_areas: List[str] = field(default_factory=list)
    pathways_credits: int = 0

    # Recommended course sequence by semester
    recommended_sequence: Dict[str, List[str]] = field(default_factory=dict)

    # Difficulty ratings for key courses (1-5)
    difficulty_ratings: Dict[str, int] = field(default_factory=dict)


# =============================================================================
# COMPUTER SCIENCE (CS) - College of Engineering
# =============================================================================

CS_REQUIREMENTS = DegreeRequirement(
    major_code="CS",
    major_name="Computer Science",
    college="College of Engineering",
    total_credits=120,

    core_courses=[
        "CS 1114",   # Intro to Software Design
        "CS 2114",   # Software Design and Data Structures
        "CS 2505",   # Computer Organization I
        "CS 2506",   # Computer Organization II
        "CS 3114",   # Data Structures and Algorithms
        "CS 3214",   # Computer Systems
        "CS 4104",   # Data and Algorithm Analysis
    ],

    choice_requirements={
        "systems_elective": ["CS 4114", "CS 4254", "CS 4284"],  # Pick 1
        "capstone": ["CS 4704", "CS 4784", "CS 4884", "CS 4274", "CS 4664", "CS 4094"],  # Pick 1
        "discrete_math": ["MATH 2534", "MATH 3034"],  # Pick 1
        "statistics": ["STAT 4705", "STAT 4714", "STAT 3005", "STAT 3104"],  # Pick 1
    },

    elective_requirements={
        "cs_electives_3000+": 4,  # 4 CS electives at 3000+ level
        "technical_electives": 2,  # 2 technical electives
    },

    math_requirements=[
        "MATH 1225",  # Calculus I
        "MATH 1226",  # Calculus II
        "MATH 2114",  # Linear Algebra
    ],

    science_requirements={
        "sequence_1": ["PHYS 2305", "PHYS 2306"],  # Physics sequence
        "sequence_2": ["CHEM 1035", "CHEM 1036"],  # OR Chemistry sequence
        "sequence_3": ["BIOL 1105", "BIOL 1106"],  # OR Biology sequence
    },

    pathways_areas=[
        "1F", "2F", "3",  # Foundations
        "5F", "5A", "6A", "6D",  # Quantitative, Critique & Practice
        "7", "7D",  # Critical Analysis, Reasoning in Social Sciences
        "10", "11",  # Ethical Reasoning, Intercultural & Global Awareness
    ],
    pathways_credits=27,

    recommended_sequence={
        "fall_1": ["CS 1114", "MATH 1225", "ENGL 1105", "Pathway"],
        "spring_1": ["CS 2114", "MATH 1226", "PHYS 2305", "Pathway"],
        "fall_2": ["CS 2505", "MATH 2114", "MATH 2534", "PHYS 2306"],
        "spring_2": ["CS 2506", "CS 3114", "STAT 4705", "Pathway"],
        "fall_3": ["CS 3214", "CS Elective", "Technical Elective", "Pathway"],
        "spring_3": ["CS 4104", "CS Systems", "CS Elective", "Pathway"],
        "fall_4": ["CS Elective", "CS Elective", "Capstone", "Pathway"],
        "spring_4": ["CS Elective", "Technical Elective", "Capstone", "Free Elective"],
    },

    difficulty_ratings={
        "CS 1114": 2,
        "CS 2114": 3,
        "CS 2505": 3,
        "CS 2506": 4,
        "CS 3114": 4,
        "CS 3214": 5,
        "CS 4104": 4,
        "CS 4114": 4,
        "CS 4254": 4,
        "CS 4284": 4,
    }
)


# =============================================================================
# ELECTRICAL & COMPUTER ENGINEERING (ECE) - College of Engineering
# =============================================================================

ECE_REQUIREMENTS = DegreeRequirement(
    major_code="ECE",
    major_name="Electrical and Computer Engineering",
    college="College of Engineering",
    total_credits=126,

    core_courses=[
        "ECE 2004",   # Electric Circuit Analysis
        "ECE 2014",   # Solid State Engineering
        "ECE 2074",   # Fundamentals of Computer Engineering
        "ECE 2514",   # Computational Engineering
        "ECE 2524",   # Open Source Software Development
        "ECE 2564",   # Embedded Systems
        "ECE 3004",   # Signals and Systems
        "ECE 3054",   # Electric Energy
        "ECE 3074",   # Digital Logic Design
        "ECE 3104",   # Fields and Waves
        "ECE 3105",   # Electromagnetic Fields
    ],

    choice_requirements={
        "track": ["Computer Engineering", "Electrical Engineering"],
        "capstone": ["ECE 4804", "ECE 4805", "ECE 4806"],
    },

    elective_requirements={
        "ece_electives": 4,
        "technical_electives": 2,
    },

    math_requirements=[
        "MATH 1225", "MATH 1226", "MATH 2114",
        "MATH 2204", "MATH 2214",
    ],

    science_requirements={
        "physics": ["PHYS 2305", "PHYS 2306"],
        "chemistry": ["CHEM 1035"],
    },

    pathways_credits=18,

    difficulty_ratings={
        "ECE 2004": 3,
        "ECE 2564": 4,
        "ECE 3004": 4,
        "ECE 3074": 3,
        "ECE 3104": 5,
    }
)


# =============================================================================
# MECHANICAL ENGINEERING (ME) - College of Engineering
# =============================================================================

ME_REQUIREMENTS = DegreeRequirement(
    major_code="ME",
    major_name="Mechanical Engineering",
    college="College of Engineering",
    total_credits=129,

    core_courses=[
        "ME 2004",    # Engineering Analysis
        "ME 2024",    # Engineering Design & Economics
        "ME 2134",    # Thermodynamics
        "ME 2204",    # Engineering Mechanics I
        "ME 2214",    # Dynamics
        "ME 2304",    # Computational Methods
        "ME 3134",    # Heat Transfer
        "ME 3144",    # Thermal-Fluid Systems
        "ME 3304",    # Machine Design I
        "ME 3404",    # Systems Dynamics & Controls
        "ME 3504",    # Fluid Mechanics
        "ME 3524",    # Experimental Methods
    ],

    choice_requirements={
        "capstone": ["ME 4015", "ME 4016"],
    },

    elective_requirements={
        "me_technical": 4,
    },

    math_requirements=[
        "MATH 1225", "MATH 1226", "MATH 2114",
        "MATH 2204", "MATH 2214",
    ],

    science_requirements={
        "physics": ["PHYS 2305", "PHYS 2306"],
        "chemistry": ["CHEM 1035", "CHEM 1036"],
    },

    difficulty_ratings={
        "ME 2134": 4,
        "ME 3134": 4,
        "ME 3504": 5,
        "ME 3404": 4,
    }
)


# =============================================================================
# BIOLOGY (BIOL) - College of Science
# =============================================================================

BIOL_REQUIREMENTS = DegreeRequirement(
    major_code="BIOL",
    major_name="Biological Sciences",
    college="College of Science",
    total_credits=120,

    core_courses=[
        "BIOL 1105",  # Principles of Biology I
        "BIOL 1106",  # Principles of Biology II
        "BIOL 2104",  # Cell and Molecular Biology
        "BIOL 2304",  # Introduction to Animal Physiology
        "BIOL 2504",  # Introduction to Evolution and Ecology
        "BIOL 3404",  # Genetics
    ],

    elective_requirements={
        "upper_level_biol": 5,
        "science_electives": 2,
    },

    math_requirements=[
        "MATH 1225", "MATH 1226",
    ],

    science_requirements={
        "chemistry": ["CHEM 1035", "CHEM 1036", "CHEM 2535", "CHEM 2536"],
        "physics": ["PHYS 2305", "PHYS 2306"],
    },

    pathways_credits=27,
)


# =============================================================================
# BUSINESS (General) - Pamplin College of Business
# =============================================================================

BUS_REQUIREMENTS = DegreeRequirement(
    major_code="BUS",
    major_name="Business",
    college="Pamplin College of Business",
    total_credits=120,

    core_courses=[
        "ACIS 2115",  # Principles of Accounting
        "ACIS 2116",  # Principles of Accounting II
        "BIT 2405",   # Business Analytics
        "BIT 2406",   # Database Management Systems
        "ECON 2005",  # Principles of Economics
        "ECON 2006",  # Principles of Economics II
        "FIN 3054",   # Introduction to Finance
        "MGT 3304",   # Management Theory & Practice
        "MKTG 3104",  # Marketing Management
    ],

    math_requirements=[
        "MATH 1525",  # OR MATH 1225
    ],

    pathways_credits=27,
)


# =============================================================================
# PSYCHOLOGY (PSYC) - College of Science
# =============================================================================

PSYC_REQUIREMENTS = DegreeRequirement(
    major_code="PSYC",
    major_name="Psychology",
    college="College of Science",
    total_credits=120,

    core_courses=[
        "PSYC 1004",  # Introduction to Psychology
        "PSYC 2004",  # Introduction to Psychological Research
        "PSYC 3014",  # Biological Bases of Behavior
        "PSYC 3024",  # Developmental Psychology
        "PSYC 3044",  # Social Psychology
        "PSYC 4204",  # History and Systems of Psychology
    ],

    elective_requirements={
        "psyc_electives": 5,
    },

    math_requirements=[
        "STAT 2004",  # OR STAT 3005
    ],

    pathways_credits=27,
)


# =============================================================================
# COMPUTATIONAL MODELING & DATA ANALYTICS (CMDA) - College of Science
# =============================================================================

CMDA_REQUIREMENTS = DegreeRequirement(
    major_code="CMDA",
    major_name="Computational Modeling and Data Analytics",
    college="College of Science",
    total_credits=120,

    core_courses=[
        "CMDA 2005",  # Computational Foundations
        "CMDA 2006",  # Foundations of Data Analytics
        "CMDA 3605",  # Data Ethics
        "CMDA 3654",  # Introductory Data Analytics & Visualization
        "CMDA 4654",  # Intermediate Data Analytics & ML
        "CMDA 4864",  # Capstone
    ],

    math_requirements=[
        "MATH 1225", "MATH 1226", "MATH 2114",
        "MATH 2204", "MATH 2534",
    ],

    elective_requirements={
        "cmda_electives": 3,
        "domain_electives": 2,
    },

    difficulty_ratings={
        "CMDA 2005": 3,
        "CMDA 3654": 3,
        "CMDA 4654": 4,
    }
)


# =============================================================================
# MAJOR REGISTRY
# =============================================================================

DEGREE_REQUIREMENTS: Dict[str, DegreeRequirement] = {
    "CS": CS_REQUIREMENTS,
    "ECE": ECE_REQUIREMENTS,
    "ME": ME_REQUIREMENTS,
    "BIOL": BIOL_REQUIREMENTS,
    "BUS": BUS_REQUIREMENTS,
    "PSYC": PSYC_REQUIREMENTS,
    "CMDA": CMDA_REQUIREMENTS,
}

# List of all supported majors for the signup form (sourced from VT catalog)
SUPPORTED_MAJORS = [
    # Pamplin College of Business
    {"code": "ACBA", "name": "Accounting & Business Analysis", "college": "Pamplin"},
    {"code": "ACIS", "name": "Accounting and Information Systems", "college": "Pamplin"},
    {"code": "BIT", "name": "Business Information Technology", "college": "Pamplin"},
    {"code": "CYMA", "name": "Cybersecurity Management and Analytics", "college": "Pamplin"},
    {"code": "EITM", "name": "Entrepreneurship, Innovation & Technology Management", "college": "Pamplin"},
    {"code": "FIN", "name": "Finance", "college": "Pamplin"},
    {"code": "FPWM", "name": "Financial Planning and Wealth Management", "college": "Pamplin"},
    {"code": "FTBD", "name": "FinTech and Big Data Analytics", "college": "Pamplin"},
    {"code": "HRM", "name": "Human Resource Management", "college": "Pamplin"},
    {"code": "HTM", "name": "Hospitality and Tourism Management", "college": "Pamplin"},
    {"code": "MCA", "name": "Management Consulting and Analytics", "college": "Pamplin"},
    {"code": "MGT", "name": "Management", "college": "Pamplin"},
    {"code": "MKTG", "name": "Marketing Management", "college": "Pamplin"},
    {"code": "PM", "name": "Property Management", "college": "Pamplin"},
    {"code": "RECP", "name": "Real Estate for Commercial Properties", "college": "Pamplin"},
    {"code": "RERP", "name": "Real Estate for Residential Properties", "college": "Pamplin"},

    # College of Engineering
    {"code": "AERO", "name": "Aerospace Engineering", "college": "Engineering"},
    {"code": "BIOM", "name": "Biomedical Engineering", "college": "Engineering"},
    {"code": "BSE", "name": "Biological Systems Engineering", "college": "Engineering"},
    {"code": "BC", "name": "Building Construction", "college": "Engineering"},
    {"code": "CHE", "name": "Chemical Engineering", "college": "Engineering"},
    {"code": "CSI", "name": "Chip-Scale Integration", "college": "Engineering"},
    {"code": "CE", "name": "Civil Engineering", "college": "Engineering"},
    {"code": "CPE", "name": "Computer Engineering", "college": "Engineering"},
    {"code": "CS", "name": "Computer Science", "college": "Engineering"},
    {"code": "CEM", "name": "Construction Engineering and Management", "college": "Engineering"},
    {"code": "CSL", "name": "Construction Safety Leadership", "college": "Engineering"},
    {"code": "CRA", "name": "Controls, Robotics & Autonomy", "college": "Engineering"},
    {"code": "DCC", "name": "Data-Centric Computing", "college": "Engineering"},
    {"code": "EE", "name": "Electrical Engineering", "college": "Engineering"},
    {"code": "EPPS", "name": "Energy & Power Electronic Systems", "college": "Engineering"},
    {"code": "ENVE", "name": "Environmental Engineering", "college": "Engineering"},
    {"code": "ISE", "name": "Industrial and Systems Engineering", "college": "Engineering"},
    {"code": "ML", "name": "Machine Learning", "college": "Engineering"},
    {"code": "MSE", "name": "Materials Science and Engineering", "college": "Engineering"},
    {"code": "ME", "name": "Mechanical Engineering", "college": "Engineering"},
    {"code": "MNS", "name": "Micro/Nanosystems", "college": "Engineering"},
    {"code": "MINE", "name": "Mining Engineering", "college": "Engineering"},
    {"code": "NC", "name": "Networking & Cybersecurity", "college": "Engineering"},
    {"code": "OE", "name": "Ocean Engineering", "college": "Engineering"},
    {"code": "SAS", "name": "Smart and Autonomous Systems", "college": "Engineering"},

    # College of Science
    {"code": "BIOC", "name": "Biochemistry", "college": "Science"},
    {"code": "BIOL", "name": "Biological Sciences", "college": "Science"},
    {"code": "CHEMBA", "name": "Chemistry (B.A.)", "college": "Science"},
    {"code": "CHEMBS", "name": "Chemistry (B.S.)", "college": "Science"},
    {"code": "CLNS", "name": "Clinical Neuroscience", "college": "Science"},
    {"code": "CBNS", "name": "Cognitive and Behavioral Neuroscience", "college": "Science"},
    {"code": "CSNS", "name": "Computational and Systems Neuroscience", "college": "Science"},
    {"code": "CMDA", "name": "Computational Modeling and Data Analytics", "college": "Science"},
    {"code": "ECON", "name": "Economics", "college": "Science"},
    {"code": "GEOS", "name": "Geosciences", "college": "Science"},
    {"code": "MATH", "name": "Mathematics", "college": "Science"},
    {"code": "MEDC", "name": "Medicinal Chemistry", "college": "Science"},
    {"code": "METR", "name": "Meteorology", "college": "Science"},
    {"code": "MICR", "name": "Microbiology", "college": "Science"},
    {"code": "NANM", "name": "Nanomedicine", "college": "Science"},
    {"code": "NANS", "name": "Nanoscience", "college": "Science"},
    {"code": "NEUR", "name": "Neuroscience", "college": "Science"},
    {"code": "PHYS", "name": "Physics", "college": "Science"},
    {"code": "POLC", "name": "Polymer Chemistry", "college": "Science"},
    {"code": "PSYC", "name": "Psychology", "college": "Science"},
    {"code": "STAT", "name": "Statistics", "college": "Science"},

    # College of Liberal Arts and Human Sciences
    {"code": "ADV", "name": "Advertising", "college": "Liberal Arts"},
    {"code": "ARAB", "name": "Arabic", "college": "Liberal Arts"},
    {"code": "CINE", "name": "Cinema", "college": "Liberal Arts"},
    {"code": "CLAS", "name": "Classical Studies", "college": "Liberal Arts"},
    {"code": "COMM", "name": "Communication", "college": "Liberal Arts"},
    {"code": "CRTC", "name": "Creative Technologies", "college": "Liberal Arts"},
    {"code": "CW", "name": "Creative Writing", "college": "Liberal Arts"},
    {"code": "CRIM", "name": "Criminology", "college": "Liberal Arts"},
    {"code": "ENGL", "name": "English", "college": "Liberal Arts"},
    {"code": "ELAE", "name": "English Language Arts Education", "college": "Liberal Arts"},
    {"code": "FR", "name": "French", "college": "Liberal Arts"},
    {"code": "GEOG", "name": "Geography", "college": "Liberal Arts"},
    {"code": "GER", "name": "German", "college": "Liberal Arts"},
    {"code": "HIST", "name": "History", "college": "Liberal Arts"},
    {"code": "HSSE", "name": "History and Social Sciences Education", "college": "Liberal Arts"},
    {"code": "HD", "name": "Human Development", "college": "Liberal Arts"},
    {"code": "HPS", "name": "Humanities for Public Service", "college": "Liberal Arts"},
    {"code": "IS", "name": "International Studies", "college": "Liberal Arts"},
    {"code": "MJ", "name": "Multimedia Journalism", "college": "Liberal Arts"},
    {"code": "MUS", "name": "Music", "college": "Liberal Arts"},
    {"code": "NSFA", "name": "National Security & Foreign Affairs", "college": "Liberal Arts"},
    {"code": "PHIL", "name": "Philosophy", "college": "Liberal Arts"},
    {"code": "PPE", "name": "Philosophy, Politics, and Economics", "college": "Liberal Arts"},
    {"code": "PSCI", "name": "Political Science", "college": "Liberal Arts"},
    {"code": "PR", "name": "Public Relations", "college": "Liberal Arts"},
    {"code": "RC", "name": "Religion and Culture", "college": "Liberal Arts"},
    {"code": "RUS", "name": "Russian", "college": "Liberal Arts"},
    {"code": "SOC", "name": "Sociology", "college": "Liberal Arts"},
    {"code": "SPAN", "name": "Spanish", "college": "Liberal Arts"},
    {"code": "TA", "name": "Theatre Arts", "college": "Liberal Arts"},
    {"code": "SW", "name": "Social Work", "college": "Liberal Arts"},

    # College of Agriculture and Life Sciences
    {"code": "AGRI", "name": "Agribusiness", "college": "Agriculture"},
    {"code": "AGEE", "name": "Agricultural and Extension Education", "college": "Agriculture"},
    {"code": "APSC", "name": "Animal and Poultry Sciences", "college": "Agriculture"},
    {"code": "CROP", "name": "Crop and Soil Sciences", "college": "Agriculture"},
    {"code": "DAIR", "name": "Dairy Science", "college": "Agriculture"},
    {"code": "ECS", "name": "Environmental Conservation & Society", "college": "Agriculture"},
    {"code": "EDS", "name": "Environmental Data Science", "college": "Agriculture"},
    {"code": "EEMP", "name": "Environmental Economics, Management, and Policy", "college": "Agriculture"},
    {"code": "EHRT", "name": "Environmental Horticulture", "college": "Agriculture"},
    {"code": "ESCI", "name": "Environmental Science", "college": "Agriculture"},
    {"code": "FCON", "name": "Fish Conservation", "college": "Agriculture"},
    {"code": "FHSE", "name": "Food and Health Systems Economics", "college": "Agriculture"},
    {"code": "FST", "name": "Food Science and Technology", "college": "Agriculture"},
    {"code": "FOR", "name": "Forestry", "college": "Agriculture"},
    {"code": "IAT", "name": "Integrated Agriculture Technologies", "college": "Agriculture"},
    {"code": "LDTS", "name": "Landscape Design and Turfgrass Science", "college": "Agriculture"},
    {"code": "PLSC", "name": "Plant Science", "college": "Agriculture"},
    {"code": "SBM", "name": "Sustainable Biomaterials", "college": "Agriculture"},
    {"code": "WLDC", "name": "Wildlife Conservation", "college": "Agriculture"},

    # College of Architecture, Arts, and Design
    {"code": "ARCH", "name": "Architecture", "college": "Architecture"},
    {"code": "ART", "name": "Art", "college": "Architecture"},
    {"code": "GRDS", "name": "Graphic Design", "college": "Architecture"},
    {"code": "IND", "name": "Industrial Design", "college": "Architecture"},
    {"code": "INTD", "name": "Interior Design", "college": "Architecture"},
    {"code": "LAR", "name": "Landscape Architecture", "college": "Architecture"},
    {"code": "SART", "name": "Studio Art", "college": "Architecture"},

    # College of Natural Resources and Environment
    {"code": "EENG", "name": "Ecological Engineering", "college": "Natural Resources"},
    {"code": "ERST", "name": "Ecological Restoration", "college": "Natural Resources"},
    {"code": "EPP", "name": "Environmental Policy and Planning", "college": "Natural Resources"},
    {"code": "ERM", "name": "Environmental Resources Management", "college": "Natural Resources"},
    {"code": "PSD", "name": "Packaging Systems and Design", "college": "Natural Resources"},
    {"code": "UAP", "name": "Urban Affairs and Planning", "college": "Natural Resources"},

    # Virginia Tech Carilion School of Medicine and related
    {"code": "NUDI", "name": "Nutrition and Dietetics", "college": "Health Sciences"},
    {"code": "PH", "name": "Public Health", "college": "Health Sciences"},
    {"code": "EHS", "name": "Exercise and Health Sciences", "college": "Health Sciences"},

    # School of Education
    {"code": "CTEA", "name": "Career and Technical Education - Agricultural Education", "college": "Education"},
    {"code": "CTE", "name": "Career and Technical Education", "college": "Education"},
    {"code": "ECDE", "name": "Early Childhood Development and Education", "college": "Education"},
    {"code": "ELEM", "name": "Elementary Education (PK-6)", "college": "Education"},
    {"code": "MAED", "name": "Mathematics Education", "college": "Education"},
    {"code": "SCED", "name": "Science Education", "college": "Education"},

    # Other Programs
    {"code": "AEM", "name": "Applied Electromagnetics", "college": "Other"},
    {"code": "APPS", "name": "Applied Public Policy Studies", "college": "Other"},
    {"code": "CED", "name": "Community Economic Development", "college": "Other"},
    {"code": "CLD", "name": "Community Leadership and Development", "college": "Other"},
    {"code": "CONS", "name": "Consumer Studies", "college": "Other"},
    {"code": "EDGE", "name": "Environment, Development, and Global Economy", "college": "Other"},
    {"code": "EEM", "name": "Event & Experience Management", "college": "Other"},
    {"code": "FMD", "name": "Fashion Merchandising and Design", "college": "Other"},
    {"code": "IR", "name": "International Relations", "college": "Other"},
    {"code": "ITD", "name": "International Trade and Development", "college": "Other"},
    {"code": "SM", "name": "Sport Management", "college": "Other"},

    # Catch-all for undeclared
    {"code": "OTHER", "name": "Other / Undeclared", "college": "General"},
]

# List of all supported minors for the signup form (sourced from VT catalog)
SUPPORTED_MINORS = [
    {"code": "ACSC", "name": "Actuarial Science"},
    {"code": "ABB", "name": "Adaptive Brain and Behavior"},
    {"code": "ADV", "name": "Advertising"},
    {"code": "AFST", "name": "Africana Studies"},
    {"code": "ABAE", "name": "Agribusiness and Entrepreneurship"},
    {"code": "AEMN", "name": "Agricultural and Applied Economics"},
    {"code": "APSC", "name": "Animal and Poultry Sciences"},
    {"code": "APEQ", "name": "Animal and Poultry Sciences Equine"},
    {"code": "APCE", "name": "Appalachian Cultures and Environments"},
    {"code": "AMUS", "name": "Applied Music"},
    {"code": "ARBC", "name": "Arabic"},
    {"code": "AHST", "name": "Art History"},
    {"code": "ASIA", "name": "Asian Studies"},
    {"code": "ASTR", "name": "Astronomy"},
    {"code": "BDS", "name": "Behavioral Decision Science"},
    {"code": "BIOD", "name": "Biodiversity Conservation"},
    {"code": "BIPH", "name": "Biological Physics"},
    {"code": "BIOL", "name": "Biological Sciences"},
    {"code": "BME", "name": "Biomedical Engineering"},
    {"code": "BLPL", "name": "Blue Planet"},
    {"code": "BUSR", "name": "Business"},
    {"code": "BSUS", "name": "Business Sustainability"},
    {"code": "CHEM", "name": "Chemistry"},
    {"code": "CHNS", "name": "Chinese Studies"},
    {"code": "CINE", "name": "Cinema"},
    {"code": "CAFS", "name": "Civic Agriculture and Food Systems"},
    {"code": "CLA", "name": "Classical Studies"},
    {"code": "CLSO", "name": "Climate and Society"},
    {"code": "CMAM", "name": "Commodity Market Analytics"},
    {"code": "CEWS", "name": "Communicating and Engaging with Science"},
    {"code": "CSE", "name": "Community Systems and Engagement"},
    {"code": "CS", "name": "Computer Science"},
    {"code": "CONS", "name": "Consumer Studies"},
    {"code": "CSES", "name": "Crop & Soil Environmental Sciences"},
    {"code": "CYBR", "name": "Cybersecurity"},
    {"code": "DASC", "name": "Dairy Science"},
    {"code": "DTDC", "name": "Data and Decisions"},
    {"code": "DTCE", "name": "Design + Technology + Creative Expression"},
    {"code": "DAIT", "name": "Development and International Trade"},
    {"code": "DMS", "name": "Digital Marketing Strategy"},
    {"code": "DST", "name": "Disability Studies"},
    {"code": "DSPS", "name": "Displacement Studies"},
    {"code": "DCE", "name": "Diversity and Community Engagement"},
    {"code": "ECDE", "name": "Early Childhood Development and Education"},
    {"code": "ECOC", "name": "Ecological Cities"},
    {"code": "ECAS", "name": "Economics"},
    {"code": "EDEI", "name": "Economics of Diversity, Equity, and Inclusion"},
    {"code": "EHWB", "name": "Ecosystem for Human Well-Being"},
    {"code": "ESM", "name": "Engineering Science & Mechanics"},
    {"code": "CENG", "name": "English - Creative Writing"},
    {"code": "ENT", "name": "Entomology"},
    {"code": "ENVG", "name": "Entrepreneurship - New Venture Growth"},
    {"code": "EECO", "name": "Environmental Economics"},
    {"code": "EPP", "name": "Environmental Policy and Planning"},
    {"code": "ENSC", "name": "Environmental Science"},
    {"code": "ESGA", "name": "Environmental, Social and Governance Analytics"},
    {"code": "EEMG", "name": "Event & Experience Management"},
    {"code": "FRMT", "name": "Fermentation"},
    {"code": "FIN", "name": "Finance"},
    {"code": "FST", "name": "Food Science and Technology"},
    {"code": "FAS", "name": "Food, Agriculture, and Society"},
    {"code": "FORS", "name": "Forestry"},
    {"code": "FR", "name": "French"},
    {"code": "FRBS", "name": "French for Business"},
    {"code": "GST", "name": "Gender, Science and Technology"},
    {"code": "GIS", "name": "Geographic Information Science"},
    {"code": "GISG", "name": "Geographic Information Science (GIS-G) Meteorology/Geography Majors"},
    {"code": "GEOG", "name": "Geography"},
    {"code": "GEOS", "name": "Geosciences"},
    {"code": "GER", "name": "German"},
    {"code": "GDPE", "name": "Global Development and Political Economy"},
    {"code": "GLBE", "name": "Global Engagement"},
    {"code": "GFSH", "name": "Global Food Security and Health"},
    {"code": "GREN", "name": "Green Engineering"},
    {"code": "HCOM", "name": "Health Communication"},
    {"code": "HIST", "name": "History"},
    {"code": "HONO", "name": "Honors Collaborative Discovery"},
    {"code": "HORT", "name": "Horticulture"},
    {"code": "HOSO", "name": "Housing and Society"},
    {"code": "HCI", "name": "Human-Computer Interaction"},
    {"code": "HSE", "name": "Humanities, Science and Environment"},
    {"code": "NDIG", "name": "Indigenous Studies"},
    {"code": "IDS", "name": "Industrial Design"},
    {"code": "ISDA", "name": "Integrated Security"},
    {"code": "IHW", "name": "Integrative Health and Wellness"},
    {"code": "IB", "name": "International Business"},
    {"code": "IREL", "name": "International Relations"},
    {"code": "IS", "name": "International Studies"},
    {"code": "ITAL", "name": "Italian"},
    {"code": "JPNS", "name": "Japanese Studies"},
    {"code": "JUD", "name": "Judaic Studies"},
    {"code": "LAR", "name": "Landscape Architecture"},
    {"code": "LCPS", "name": "Language and Culture for the Practice of Science"},
    {"code": "LNGS", "name": "Language Sciences"},
    {"code": "LAS", "name": "Leadership and Service"},
    {"code": "ILRM", "name": "Leadership and Social Change"},
    {"code": "LMCC", "name": "Leadership, Corps of Cadets"},
    {"code": "LIT", "name": "Literature"},
    {"code": "MTSC", "name": "Materials in Society"},
    {"code": "MATH", "name": "Mathematics"},
    {"code": "MSOC", "name": "Medicine and Society"},
    {"code": "MTRG", "name": "Meteorology"},
    {"code": "MEST", "name": "Middle East Studies"},
    {"code": "MMJS", "name": "Music (Jazz Studies)"},
    {"code": "MUSC", "name": "Music"},
    {"code": "MMTX", "name": "Music (Technology Emphasis)"},
    {"code": "MPTC", "name": "Music Production, Technology, and Composition"},
    {"code": "NANO", "name": "Nanoscience"},
    {"code": "NSFA", "name": "National Security and Foreign Affairs"},
    {"code": "NRR", "name": "Natural Resources Recreation"},
    {"code": "NAVE", "name": "Naval Engineering"},
    {"code": "MN", "name": "Naval Leadership"},
    {"code": "NE", "name": "Nuclear Engineering"},
    {"code": "BOLD", "name": "Organizational Leadership"},
    {"code": "PSD", "name": "Packaging Systems & Design"},
    {"code": "PSUS", "name": "Pathways to Sustainability"},
    {"code": "PSSJ", "name": "Peace Studies and Social Justice"},
    {"code": "PHIL", "name": "Philosophy"},
    {"code": "PPEM", "name": "Philosophy, Politics, and Economics"},
    {"code": "PHYS", "name": "Physics"},
    {"code": "PHS", "name": "Plant Health Sciences"},
    {"code": "PSCI", "name": "Political Science"},
    {"code": "POPC", "name": "Popular Culture"},
    {"code": "PRFS", "name": "Professional Sales"},
    {"code": "PM", "name": "Property Management"},
    {"code": "PSYC", "name": "Psychology"},
    {"code": "PH", "name": "Public Health"},
    {"code": "QUAN", "name": "Quantum Information Science and Engineering"},
    {"code": "REAL", "name": "Real Estate"},
    {"code": "REL", "name": "Religion"},
    {"code": "MRJ", "name": "Religion and Journalism"},
    {"code": "RUS", "name": "Russian"},
    {"code": "SCED", "name": "Science Education"},
    {"code": "STL", "name": "Science, Technology, and Law"},
    {"code": "SOC", "name": "Sociology"},
    {"code": "SPAN", "name": "Spanish"},
    {"code": "STAT", "name": "Statistics"},
    {"code": "SCM", "name": "Supply Chain Management"},
    {"code": "SUST", "name": "Sustainability"},
    {"code": "SYSB", "name": "Systems Biology"},
    {"code": "CYSE", "name": "Technology, Cybersecurity, and Policy"},
    {"code": "TA", "name": "Theatre Arts"},
    {"code": "TBMH", "name": "Translational Biology, Medicine, & Health"},
    {"code": "WATR", "name": "Water: Resources, Policy, and Management"},
    {"code": "WGS", "name": "Women's and Gender Studies"},
    {"code": "NONE", "name": "No Minor"},
]

# Major concentrations/options by major code
# Only majors with concentrations are listed
MAJOR_CONCENTRATIONS = {
    # Computer Science & Related
    "CS": [
        {"code": "CS-GEN", "name": "General Computer Science"},
        {"code": "CS-SYS", "name": "Systems"},
        {"code": "CS-SEC", "name": "Security"},
        {"code": "CS-AI", "name": "Artificial Intelligence & Machine Learning"},
        {"code": "CS-HCI", "name": "Human-Computer Interaction"},
        {"code": "CS-DATA", "name": "Data & Analytics"},
        {"code": "CS-TIC", "name": "Theory & Algorithms"},
    ],
    "CPE": [
        {"code": "CPE-GEN", "name": "General Computer Engineering"},
        {"code": "CPE-EMB", "name": "Embedded Systems"},
        {"code": "CPE-NET", "name": "Networks & Security"},
    ],
    "EE": [
        {"code": "EE-GEN", "name": "General Electrical Engineering"},
        {"code": "EE-POW", "name": "Power & Energy Systems"},
        {"code": "EE-COMM", "name": "Communications & Signal Processing"},
        {"code": "EE-CTRL", "name": "Controls & Robotics"},
        {"code": "EE-MICRO", "name": "Microelectronics"},
    ],

    # Business - Pamplin
    "MKTG": [
        {"code": "MKTG-GEN", "name": "General Marketing"},
        {"code": "MKTG-DIG", "name": "Digital Marketing Strategy"},
        {"code": "MKTG-SAL", "name": "Professional Sales"},
    ],
    "FIN": [
        {"code": "FIN-GEN", "name": "General Finance"},
        {"code": "FIN-CFA", "name": "Investment Management & CFA"},
        {"code": "FIN-CORP", "name": "Corporate Finance"},
        {"code": "FIN-BANK", "name": "Banking"},
    ],
    "MGT": [
        {"code": "MGT-GEN", "name": "General Management"},
        {"code": "MGT-ENT", "name": "Entrepreneurship"},
        {"code": "MGT-OP", "name": "Operations Management"},
        {"code": "MGT-SCM", "name": "Supply Chain Management"},
    ],
    "ACIS": [
        {"code": "ACIS-ACC", "name": "Accounting"},
        {"code": "ACIS-IS", "name": "Information Systems"},
        {"code": "ACIS-CPA", "name": "CPA Track"},
    ],
    "BIT": [
        {"code": "BIT-GEN", "name": "General Business IT"},
        {"code": "BIT-DSS", "name": "Decision Support Systems"},
        {"code": "BIT-OM", "name": "Operations Management"},
    ],
    "HTM": [
        {"code": "HTM-GEN", "name": "General Hospitality & Tourism"},
        {"code": "HTM-EVT", "name": "Event Management"},
        {"code": "HTM-RES", "name": "Restaurant Management"},
        {"code": "HTM-HOTEL", "name": "Hotel Management"},
    ],

    # Engineering
    "ME": [
        {"code": "ME-GEN", "name": "General Mechanical Engineering"},
        {"code": "ME-AUTO", "name": "Automotive"},
        {"code": "ME-AERO", "name": "Aerospace Applications"},
        {"code": "ME-THERM", "name": "Thermal & Fluid Systems"},
        {"code": "ME-MFG", "name": "Manufacturing"},
        {"code": "ME-BIO", "name": "Biomechanics"},
    ],
    "CE": [
        {"code": "CE-GEN", "name": "General Civil Engineering"},
        {"code": "CE-STR", "name": "Structural Engineering"},
        {"code": "CE-TRAN", "name": "Transportation"},
        {"code": "CE-GEO", "name": "Geotechnical"},
        {"code": "CE-WR", "name": "Water Resources"},
    ],
    "CHE": [
        {"code": "CHE-GEN", "name": "General Chemical Engineering"},
        {"code": "CHE-BIO", "name": "Biochemical"},
        {"code": "CHE-ENV", "name": "Environmental"},
        {"code": "CHE-MAT", "name": "Materials"},
    ],
    "AERO": [
        {"code": "AERO-GEN", "name": "General Aerospace Engineering"},
        {"code": "AERO-PROP", "name": "Propulsion"},
        {"code": "AERO-STRUCT", "name": "Structures"},
        {"code": "AERO-DYN", "name": "Aerodynamics"},
    ],
    "ISE": [
        {"code": "ISE-GEN", "name": "General Industrial & Systems"},
        {"code": "ISE-OR", "name": "Operations Research"},
        {"code": "ISE-HF", "name": "Human Factors"},
        {"code": "ISE-MFG", "name": "Manufacturing Systems"},
    ],
    "BSE": [
        {"code": "BSE-GEN", "name": "General Biological Systems"},
        {"code": "BSE-BIO", "name": "Bioprocess Engineering"},
        {"code": "BSE-ENV", "name": "Environmental Engineering"},
        {"code": "BSE-FOOD", "name": "Food & Bioprocess"},
    ],
    "BIOM": [
        {"code": "BIOM-GEN", "name": "General Biomedical Engineering"},
        {"code": "BIOM-BM", "name": "Biomechanics"},
        {"code": "BIOM-BI", "name": "Bioinstrumentation"},
        {"code": "BIOM-TISS", "name": "Tissue Engineering"},
    ],

    # Science
    "BIOL": [
        {"code": "BIOL-GEN", "name": "General Biology"},
        {"code": "BIOL-CELL", "name": "Cell & Molecular Biology"},
        {"code": "BIOL-ECO", "name": "Ecology & Conservation"},
        {"code": "BIOL-MED", "name": "Pre-Medical"},
        {"code": "BIOL-MICR", "name": "Microbiology"},
    ],
    "CHEMBS": [
        {"code": "CHEM-GEN", "name": "General Chemistry"},
        {"code": "CHEM-BIO", "name": "Biochemistry"},
        {"code": "CHEM-MAT", "name": "Materials Chemistry"},
        {"code": "CHEM-ENV", "name": "Environmental Chemistry"},
    ],
    "PSYC": [
        {"code": "PSYC-GEN", "name": "General Psychology"},
        {"code": "PSYC-CLIN", "name": "Clinical Psychology"},
        {"code": "PSYC-COG", "name": "Cognitive Psychology"},
        {"code": "PSYC-DEV", "name": "Developmental Psychology"},
        {"code": "PSYC-SOC", "name": "Social Psychology"},
        {"code": "PSYC-IO", "name": "Industrial-Organizational"},
    ],
    "ECON": [
        {"code": "ECON-GEN", "name": "General Economics"},
        {"code": "ECON-FIN", "name": "Financial Economics"},
        {"code": "ECON-INT", "name": "International Economics"},
        {"code": "ECON-POL", "name": "Policy Analysis"},
    ],
    "MATH": [
        {"code": "MATH-GEN", "name": "General Mathematics"},
        {"code": "MATH-APP", "name": "Applied Mathematics"},
        {"code": "MATH-STAT", "name": "Statistics"},
        {"code": "MATH-ACT", "name": "Actuarial Science"},
        {"code": "MATH-COMP", "name": "Computational"},
    ],
    "STAT": [
        {"code": "STAT-GEN", "name": "General Statistics"},
        {"code": "STAT-BIO", "name": "Biostatistics"},
        {"code": "STAT-DATA", "name": "Data Science"},
    ],
    "CMDA": [
        {"code": "CMDA-GEN", "name": "General CMDA"},
        {"code": "CMDA-DS", "name": "Data Science"},
        {"code": "CMDA-OR", "name": "Operations Research"},
        {"code": "CMDA-BIO", "name": "Computational Biology"},
    ],
    "PHYS": [
        {"code": "PHYS-GEN", "name": "General Physics"},
        {"code": "PHYS-ASTRO", "name": "Astrophysics"},
        {"code": "PHYS-BIO", "name": "Biophysics"},
        {"code": "PHYS-COMP", "name": "Computational Physics"},
    ],

    # Liberal Arts
    "COMM": [
        {"code": "COMM-GEN", "name": "General Communication"},
        {"code": "COMM-PR", "name": "Public Relations"},
        {"code": "COMM-ADV", "name": "Advertising"},
        {"code": "COMM-JOUR", "name": "Journalism"},
    ],
    "ENGL": [
        {"code": "ENGL-GEN", "name": "General English"},
        {"code": "ENGL-CW", "name": "Creative Writing"},
        {"code": "ENGL-LIT", "name": "Literature"},
        {"code": "ENGL-RHT", "name": "Rhetoric & Writing"},
    ],
    "PSCI": [
        {"code": "PSCI-GEN", "name": "General Political Science"},
        {"code": "PSCI-LAW", "name": "Pre-Law"},
        {"code": "PSCI-IR", "name": "International Relations"},
        {"code": "PSCI-POL", "name": "American Politics"},
    ],
    "SOC": [
        {"code": "SOC-GEN", "name": "General Sociology"},
        {"code": "SOC-CRIM", "name": "Criminology"},
        {"code": "SOC-FAM", "name": "Family & Community"},
    ],
    "HIST": [
        {"code": "HIST-GEN", "name": "General History"},
        {"code": "HIST-US", "name": "American History"},
        {"code": "HIST-EUR", "name": "European History"},
        {"code": "HIST-GLOB", "name": "Global History"},
    ],

    # Architecture & Design
    "ARCH": [
        {"code": "ARCH-GEN", "name": "General Architecture"},
        {"code": "ARCH-URB", "name": "Urban Design"},
        {"code": "ARCH-SUST", "name": "Sustainable Design"},
    ],
    "IND": [
        {"code": "IND-GEN", "name": "General Industrial Design"},
        {"code": "IND-PROD", "name": "Product Design"},
        {"code": "IND-UX", "name": "User Experience"},
    ],
    "INTD": [
        {"code": "INTD-GEN", "name": "General Interior Design"},
        {"code": "INTD-COM", "name": "Commercial Design"},
        {"code": "INTD-RES", "name": "Residential Design"},
    ],

    # Agriculture & Life Sciences
    "APSC": [
        {"code": "APSC-GEN", "name": "General Animal Science"},
        {"code": "APSC-PREVET", "name": "Pre-Veterinary"},
        {"code": "APSC-PROD", "name": "Animal Production"},
        {"code": "APSC-EQ", "name": "Equine Science"},
    ],
    "FST": [
        {"code": "FST-GEN", "name": "General Food Science"},
        {"code": "FST-SAFE", "name": "Food Safety"},
        {"code": "FST-PROC", "name": "Food Processing"},
    ],

    # Health Sciences
    "NUDI": [
        {"code": "NUDI-GEN", "name": "General Nutrition"},
        {"code": "NUDI-DIET", "name": "Dietetics"},
        {"code": "NUDI-SPORT", "name": "Sports Nutrition"},
    ],
    "PH": [
        {"code": "PH-GEN", "name": "General Public Health"},
        {"code": "PH-EPI", "name": "Epidemiology"},
        {"code": "PH-HP", "name": "Health Promotion"},
    ],
}

def get_concentrations(major_code: str) -> list:
    """Get available concentrations for a major"""
    return MAJOR_CONCENTRATIONS.get(major_code.upper(), [])


def get_requirements(major_code: str) -> Optional[DegreeRequirement]:
    """Get degree requirements for a major"""
    return DEGREE_REQUIREMENTS.get(major_code.upper())


def get_major_info(major_code: str) -> Optional[dict]:
    """Get basic info about a major"""
    for major in SUPPORTED_MAJORS:
        if major["code"] == major_code.upper():
            return major
    return None


def calculate_semesters_remaining(start_year: int, grad_year: int, current_semester: str = "fall") -> int:
    """Calculate how many semesters the student has remaining"""
    from datetime import datetime
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Determine current semester
    if current_month < 5:
        current_sem = "spring"
        year_offset = 0
    elif current_month < 8:
        current_sem = "summer"
        year_offset = 0.5
    else:
        current_sem = "fall"
        year_offset = 0.5

    current_position = current_year + year_offset
    grad_position = grad_year + 0.5  # Graduate after spring

    remaining = (grad_position - current_position) * 2
    return max(0, int(remaining))


def get_recommended_courses_for_semester(
    major_code: str,
    completed_courses: List[str],
    semester_number: int
) -> List[str]:
    """Get recommended courses for a specific semester based on major and progress"""
    req = get_requirements(major_code)
    if not req:
        return []

    # Map semester number to key
    semester_keys = [
        "fall_1", "spring_1", "fall_2", "spring_2",
        "fall_3", "spring_3", "fall_4", "spring_4"
    ]

    if semester_number < 1 or semester_number > len(semester_keys):
        return []

    key = semester_keys[semester_number - 1]
    recommended = req.recommended_sequence.get(key, [])

    # Filter out completed courses
    completed_set = set(c.upper() for c in completed_courses)
    return [c for c in recommended if c.upper() not in completed_set]


def check_graduation_progress(
    major_code: str,
    completed_courses: List[str],
    in_progress: List[str] = None
) -> dict:
    """Check how close a student is to graduation"""
    req = get_requirements(major_code)
    if not req:
        return {"error": "Major not found"}

    completed_set = set(c.upper() for c in completed_courses)
    in_progress_set = set(c.upper() for c in (in_progress or []))
    all_courses = completed_set | in_progress_set

    # Check core courses
    core_completed = [c for c in req.core_courses if c in completed_set]
    core_in_progress = [c for c in req.core_courses if c in in_progress_set]
    core_remaining = [c for c in req.core_courses if c not in all_courses]

    # Check math requirements
    math_completed = [c for c in req.math_requirements if c in completed_set]
    math_remaining = [c for c in req.math_requirements if c not in all_courses]

    # Check choice requirements
    choices_satisfied = {}
    for choice_name, options in req.choice_requirements.items():
        satisfied = any(c in all_courses for c in options)
        choices_satisfied[choice_name] = {
            "satisfied": satisfied,
            "options": options,
            "completed": [c for c in options if c in completed_set]
        }

    # Calculate overall progress
    total_required = len(req.core_courses) + len(req.math_requirements) + len(req.choice_requirements)
    total_done = len(core_completed) + len(math_completed) + sum(1 for c in choices_satisfied.values() if c["satisfied"])

    progress_percent = (total_done / total_required * 100) if total_required > 0 else 0

    return {
        "major": req.major_name,
        "progress_percent": round(progress_percent, 1),
        "core": {
            "completed": core_completed,
            "in_progress": core_in_progress,
            "remaining": core_remaining,
            "total": len(req.core_courses)
        },
        "math": {
            "completed": math_completed,
            "remaining": math_remaining,
            "total": len(req.math_requirements)
        },
        "choices": choices_satisfied,
        "total_credits_required": req.total_credits,
    }
