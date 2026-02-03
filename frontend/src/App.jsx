/**
 * VT Academic Optimizer - Comprehensive Course Planner
 * =====================================================
 * Drag & drop planner with AI optimization
 */

import { useState, useEffect, useCallback, useMemo } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Auth helpers
const getToken = () => localStorage.getItem('token')
const setToken = (token) => localStorage.setItem('token', token)
const removeToken = () => localStorage.removeItem('token')
const getUser = () => JSON.parse(localStorage.getItem('user') || 'null')
const setUserStorage = (user) => localStorage.setItem('user', JSON.stringify(user))
const removeUser = () => localStorage.removeItem('user')

// ============================================================================
// DEFAULT COURSE DATA (loaded from backend, this is fallback)
// ============================================================================

const DEFAULT_COURSES = {
  // CS CORE REQUIREMENTS
  "CS 1114": {
    name: "Intro to Software Design",
    prereqs: [],
    credits: 3,
    category: "cs_core",
    difficulty: 2,
    workload: 2,
    required: true,
    professors: [
      { name: "Dr. McQuain", rating: 4.2, avgGPA: 3.1 },
      { name: "Dr. Shaffer", rating: 3.8, avgGPA: 2.9 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["intro", "programming", "java"]
  },
  "CS 1064": {
    name: "Intro to Python",
    prereqs: [],
    credits: 2,
    category: "cs_core",
    difficulty: 1,
    workload: 1,
    required: false,
    professors: [
      { name: "Dr. Barnette", rating: 4.5, avgGPA: 3.4 }
    ],
    timeSlots: ["10:00 AM", "1:00 PM"],
    tags: ["intro", "python", "easy"]
  },
  "CS 2104": {
    name: "Problem Solving in CS",
    prereqs: ["CS 1114"],
    credits: 3,
    category: "cs_core",
    difficulty: 2,
    workload: 2,
    required: true,
    professors: [
      { name: "Dr. Shaffer", rating: 3.9, avgGPA: 3.0 }
    ],
    timeSlots: ["9:00 AM", "2:00 PM"],
    tags: ["theory", "problem-solving"]
  },
  "CS 2114": {
    name: "Software Design & Data Structures",
    prereqs: ["CS 1114"],
    credits: 3,
    category: "cs_core",
    difficulty: 3,
    workload: 4,
    required: true,
    professors: [
      { name: "Dr. McQuain", rating: 4.0, avgGPA: 3.2 },
      { name: "Dr. Shaffer", rating: 3.5, avgGPA: 2.8 }
    ],
    timeSlots: ["8:00 AM", "10:00 AM", "1:00 PM", "3:00 PM"],
    tags: ["data-structures", "oop", "heavy"]
  },
  "CS 2505": {
    name: "Computer Organization I",
    prereqs: ["CS 1114"],
    credits: 3,
    category: "cs_core",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Butt", rating: 3.7, avgGPA: 2.9 },
      { name: "Dr. Jones", rating: 4.1, avgGPA: 3.1 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["systems", "assembly", "hardware"]
  },
  "CS 2506": {
    name: "Computer Organization II",
    prereqs: ["CS 2505", "CS 2114"],
    credits: 3,
    category: "cs_core",
    difficulty: 4,
    workload: 4,
    required: true,
    professors: [
      { name: "Dr. Butt", rating: 3.6, avgGPA: 2.7 }
    ],
    timeSlots: ["10:00 AM", "1:00 PM"],
    tags: ["systems", "c", "hardware", "heavy"]
  },
  "CS 3114": {
    name: "Data Structures & Algorithms",
    prereqs: ["CS 2114", "CS 2505"],
    credits: 3,
    category: "cs_core",
    difficulty: 4,
    workload: 5,
    required: true,
    professors: [
      { name: "Dr. Back", rating: 4.3, avgGPA: 3.0 },
      { name: "Dr. Shaffer", rating: 3.4, avgGPA: 2.6 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["algorithms", "data-structures", "heavy", "weedout"]
  },
  "CS 3214": {
    name: "Computer Systems",
    prereqs: ["CS 2506", "CS 3114"],
    credits: 3,
    category: "cs_core",
    difficulty: 5,
    workload: 5,
    required: true,
    professors: [
      { name: "Dr. Back", rating: 4.1, avgGPA: 2.8 }
    ],
    timeSlots: ["10:00 AM", "2:00 PM"],
    tags: ["systems", "c", "linux", "very-heavy", "weedout"]
  },
  "CS 3304": {
    name: "Comparative Languages",
    prereqs: ["CS 2114"],
    credits: 3,
    category: "cs_core",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Edwards", rating: 4.0, avgGPA: 3.1 }
    ],
    timeSlots: ["11:00 AM", "3:00 PM"],
    tags: ["languages", "theory"]
  },
  "CS 4104": {
    name: "Data & Algorithm Analysis",
    prereqs: ["CS 3114", "MATH 2114"],
    credits: 3,
    category: "cs_core",
    difficulty: 4,
    workload: 4,
    required: true,
    professors: [
      { name: "Dr. Fox", rating: 3.5, avgGPA: 2.7 },
      { name: "Dr. Heath", rating: 4.2, avgGPA: 3.0 }
    ],
    timeSlots: ["9:00 AM", "1:00 PM"],
    tags: ["algorithms", "theory", "math-heavy"]
  },

  // CS ELECTIVES
  "CS 3414": {
    name: "Numerical Methods",
    prereqs: ["CS 2114", "MATH 2114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Watson", rating: 4.0, avgGPA: 3.2 }
    ],
    timeSlots: ["10:00 AM", "2:00 PM"],
    tags: ["math", "numerical", "matlab"]
  },
  "CS 4114": {
    name: "Operating Systems",
    prereqs: ["CS 3214"],
    credits: 3,
    category: "cs_elective",
    difficulty: 4,
    workload: 4,
    required: false,
    professors: [
      { name: "Dr. Back", rating: 4.2, avgGPA: 2.9 }
    ],
    timeSlots: ["11:00 AM", "3:00 PM"],
    tags: ["systems", "os", "heavy"]
  },
  "CS 4124": {
    name: "Machine Learning",
    prereqs: ["CS 3114", "STAT 3006"],
    credits: 3,
    category: "cs_elective",
    difficulty: 4,
    workload: 4,
    required: false,
    professors: [
      { name: "Dr. Huang", rating: 4.4, avgGPA: 3.3 }
    ],
    timeSlots: ["10:00 AM", "2:00 PM"],
    tags: ["ml", "ai", "python", "hot"]
  },
  "CS 4254": {
    name: "Computer Networks",
    prereqs: ["CS 3214"],
    credits: 3,
    category: "cs_elective",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Yang", rating: 4.1, avgGPA: 3.1 }
    ],
    timeSlots: ["9:00 AM", "1:00 PM"],
    tags: ["networks", "systems"]
  },
  "CS 4264": {
    name: "Computer Security",
    prereqs: ["CS 3214"],
    credits: 3,
    category: "cs_elective",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Yao", rating: 4.3, avgGPA: 3.2 }
    ],
    timeSlots: ["11:00 AM", "3:00 PM"],
    tags: ["security", "hot", "industry"]
  },
  "CS 4284": {
    name: "Systems Capstone",
    prereqs: ["CS 3214"],
    credits: 3,
    category: "cs_elective",
    difficulty: 4,
    workload: 4,
    required: false,
    professors: [
      { name: "Dr. Back", rating: 4.0, avgGPA: 3.0 }
    ],
    timeSlots: ["2:00 PM"],
    tags: ["capstone", "systems", "project"]
  },
  "CS 4604": {
    name: "Database Systems",
    prereqs: ["CS 3114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Ramakrishnan", rating: 4.5, avgGPA: 3.3 }
    ],
    timeSlots: ["10:00 AM", "2:00 PM"],
    tags: ["databases", "sql", "industry", "easy-elective"]
  },
  "CS 4624": {
    name: "Multimedia & Info Access",
    prereqs: ["CS 3114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 2,
    workload: 2,
    required: false,
    professors: [
      { name: "Dr. Fox", rating: 4.2, avgGPA: 3.5 }
    ],
    timeSlots: ["11:00 AM", "3:00 PM"],
    tags: ["multimedia", "easy-elective"]
  },
  "CS 4644": {
    name: "Creative Computing",
    prereqs: ["CS 2114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 2,
    workload: 2,
    required: false,
    professors: [
      { name: "Dr. Quek", rating: 4.6, avgGPA: 3.6 }
    ],
    timeSlots: ["1:00 PM", "4:00 PM"],
    tags: ["creative", "fun", "easy-elective"]
  },
  "CS 4804": {
    name: "Intro to AI",
    prereqs: ["CS 3114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Cao", rating: 4.4, avgGPA: 3.4 }
    ],
    timeSlots: ["9:00 AM", "1:00 PM"],
    tags: ["ai", "theory", "hot"]
  },
  "CS 4824": {
    name: "Machine Learning II",
    prereqs: ["CS 3114", "MATH 2114"],
    credits: 3,
    category: "cs_elective",
    difficulty: 4,
    workload: 4,
    required: false,
    professors: [
      { name: "Dr. Huang", rating: 4.3, avgGPA: 3.1 }
    ],
    timeSlots: ["10:00 AM"],
    tags: ["ml", "ai", "advanced", "heavy"]
  },

  // MATH REQUIREMENTS
  "MATH 1225": {
    name: "Calculus I",
    prereqs: [],
    credits: 3,
    category: "math",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Arnold", rating: 4.0, avgGPA: 2.8 },
      { name: "Dr. Brown", rating: 3.5, avgGPA: 2.5 }
    ],
    timeSlots: ["8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM"],
    tags: ["math", "calculus"]
  },
  "MATH 1226": {
    name: "Calculus II",
    prereqs: ["MATH 1225"],
    credits: 3,
    category: "math",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Arnold", rating: 3.9, avgGPA: 2.7 },
      { name: "Dr. Smith", rating: 4.2, avgGPA: 3.0 }
    ],
    timeSlots: ["8:00 AM", "10:00 AM", "1:00 PM", "3:00 PM"],
    tags: ["math", "calculus"]
  },
  "MATH 2114": {
    name: "Linear Algebra",
    prereqs: ["MATH 1226"],
    credits: 3,
    category: "math",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Lee", rating: 4.3, avgGPA: 3.1 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["math", "linear-algebra", "useful"]
  },
  "MATH 2204": {
    name: "Multivariable Calculus",
    prereqs: ["MATH 1226"],
    credits: 3,
    category: "math",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Kim", rating: 4.1, avgGPA: 2.9 }
    ],
    timeSlots: ["10:00 AM", "1:00 PM"],
    tags: ["math", "calculus"]
  },
  "MATH 3134": {
    name: "Applied Combinatorics",
    prereqs: ["MATH 1226"],
    credits: 3,
    category: "math",
    difficulty: 3,
    workload: 2,
    required: true,
    professors: [
      { name: "Dr. Green", rating: 4.4, avgGPA: 3.2 }
    ],
    timeSlots: ["11:00 AM", "2:00 PM"],
    tags: ["math", "discrete", "cs-related"]
  },
  "STAT 3006": {
    name: "Statistics for Engineers",
    prereqs: ["MATH 1226"],
    credits: 3,
    category: "math",
    difficulty: 2,
    workload: 2,
    required: true,
    professors: [
      { name: "Dr. Taylor", rating: 4.5, avgGPA: 3.4 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "1:00 PM", "3:00 PM"],
    tags: ["stats", "easy", "useful"]
  },

  // SCIENCE REQUIREMENTS
  "PHYS 2305": {
    name: "Physics I",
    prereqs: ["MATH 1225"],
    credits: 4,
    category: "science",
    difficulty: 3,
    workload: 3,
    required: true,
    professors: [
      { name: "Dr. Parker", rating: 3.8, avgGPA: 2.8 }
    ],
    timeSlots: ["8:00 AM", "10:00 AM", "1:00 PM"],
    tags: ["physics", "lab"]
  },
  "PHYS 2306": {
    name: "Physics II",
    prereqs: ["PHYS 2305", "MATH 1226"],
    credits: 4,
    category: "science",
    difficulty: 3,
    workload: 3,
    required: false,
    professors: [
      { name: "Dr. Wilson", rating: 4.0, avgGPA: 2.9 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["physics", "lab", "e&m"]
  },
  "CHEM 1035": {
    name: "General Chemistry",
    prereqs: [],
    credits: 4,
    category: "science",
    difficulty: 2,
    workload: 2,
    required: false,
    professors: [
      { name: "Dr. Adams", rating: 4.2, avgGPA: 3.1 }
    ],
    timeSlots: ["8:00 AM", "10:00 AM", "1:00 PM"],
    tags: ["chemistry", "lab", "easy-science"]
  },
  "BIOL 1105": {
    name: "Principles of Biology",
    prereqs: [],
    credits: 4,
    category: "science",
    difficulty: 2,
    workload: 2,
    required: false,
    professors: [
      { name: "Dr. Clark", rating: 4.3, avgGPA: 3.2 }
    ],
    timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"],
    tags: ["biology", "lab", "easy-science"]
  },

  // PATHWAYS
  "ENGL 1105": { name: "First-Year Writing", prereqs: [], credits: 3, category: "pathway_discourse", difficulty: 1, workload: 2, required: true, professors: [{ name: "Various", rating: 4.0, avgGPA: 3.3 }], timeSlots: ["9:00 AM", "11:00 AM", "1:00 PM", "3:00 PM"], tags: ["writing", "easy"] },
  "COMM 1016": { name: "Public Speaking", prereqs: [], credits: 3, category: "pathway_discourse", difficulty: 1, workload: 1, required: true, professors: [{ name: "Various", rating: 4.2, avgGPA: 3.5 }], timeSlots: ["10:00 AM", "2:00 PM"], tags: ["speaking", "easy"] },
  "PHIL 1304": { name: "Ethics & Philosophy", prereqs: [], credits: 3, category: "pathway_critical", difficulty: 2, workload: 2, required: true, professors: [{ name: "Dr. White", rating: 4.1, avgGPA: 3.2 }], timeSlots: ["11:00 AM", "3:00 PM"], tags: ["philosophy", "ethics"] },
  "MUSI 1004": { name: "Music Appreciation", prereqs: [], credits: 3, category: "pathway_arts", difficulty: 1, workload: 1, required: true, professors: [{ name: "Dr. Davis", rating: 4.6, avgGPA: 3.7 }], timeSlots: ["10:00 AM", "1:00 PM", "4:00 PM"], tags: ["music", "easy", "fun"] },
  "PSYC 1004": { name: "Intro to Psychology", prereqs: [], credits: 3, category: "pathway_society", difficulty: 1, workload: 1, required: true, professors: [{ name: "Dr. Miller", rating: 4.4, avgGPA: 3.4 }], timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"], tags: ["psychology", "easy", "interesting"] },
  "ECON 2005": { name: "Principles of Economics", prereqs: [], credits: 3, category: "pathway_society", difficulty: 2, workload: 2, required: false, professors: [{ name: "Dr. Johnson", rating: 4.0, avgGPA: 3.0 }], timeSlots: ["10:00 AM", "1:00 PM"], tags: ["economics", "useful"] },
  "HIST 1115": { name: "US History", prereqs: [], credits: 3, category: "pathway_reasoning", difficulty: 2, workload: 2, required: true, professors: [{ name: "Dr. Thompson", rating: 4.2, avgGPA: 3.3 }], timeSlots: ["9:00 AM", "11:00 AM", "2:00 PM"], tags: ["history"] },
}

const CATEGORY_INFO = {
  cs_core: { name: "CS Core", color: "blue", required: true },
  cs_intro: { name: "CS Intro", color: "slate", required: false },
  cs_elective: { name: "CS Electives", color: "indigo", required: false },
  cs_theory: { name: "CS Theory", color: "violet", required: true },
  cs_systems: { name: "CS Systems", color: "purple", required: true },
  capstone: { name: "Capstone", color: "pink", required: true },
  math_core: { name: "Math Core", color: "green", required: true },
  math_discrete: { name: "Discrete Math", color: "lime", required: true },
  math_elective: { name: "Math Elective", color: "emerald", required: false },
  stats: { name: "Statistics", color: "teal", required: true },
  stats_elective: { name: "Stats Elective", color: "cyan", required: false },
  science: { name: "Science", color: "amber", required: true },
  pathways: { name: "Pathways", color: "orange", required: true },
  engineering: { name: "Engineering", color: "slate", required: false },
}

// VT CS Degree Requirements (120 credits total)
const DEGREE_REQUIREMENTS = {
  cs_core: {
    name: "CS Core",
    required: ["CS 1114", "CS 2114", "CS 2505", "CS 2506", "CS 3114", "CS 3214"],
    credits: 18,
    color: "blue"
  },
  cs_systems: {
    name: "Systems &Tic",
    required: ["CS 4104"],
    choose: 1,
    from: ["CS 4114", "CS 4254", "CS 4284"],
    credits: 6,
    color: "indigo"
  },
  cs_electives: {
    name: "CS Electives",
    minCredits: 9,
    minCourses: 3,
    from: "cs_elective",  // Any CS 3000/4000 level
    color: "purple"
  },
  math_core: {
    name: "Math Core",
    required: ["MATH 1225", "MATH 1226", "MATH 2114"],
    credits: 10,
    color: "green"
  },
  stats: {
    name: "Statistics",
    choose: 1,
    from: ["STAT 3006", "STAT 4705", "STAT 4714"],
    credits: 3,
    color: "teal"
  },
  science: {
    name: "Science",
    required: ["PHYS 2305", "PHYS 2306"],
    additionalCredits: 3,  // One more science course
    credits: 11,
    color: "emerald"
  },
  capstone: {
    name: "Capstone",
    choose: 1,
    from: ["CS 4624", "CS 4644", "CS 4974"],
    credits: 3,
    color: "pink"
  },
  pathways: {
    name: "Pathways/Gen Ed",
    minCredits: 27,
    description: "Discourse, Critical Thinking, Arts, Society, Reasoning",
    color: "orange"
  },
  free_electives: {
    name: "Free Electives",
    minCredits: 12,
    description: "Any courses to reach 120 credits",
    color: "slate"
  }
}

const SEMESTERS = [
  { id: "fall1", name: "Fall Y1", year: 1, term: "Fall" },
  { id: "spring1", name: "Spr Y1", year: 1, term: "Spring" },
  { id: "fall2", name: "Fall Y2", year: 2, term: "Fall" },
  { id: "spring2", name: "Spr Y2", year: 2, term: "Spring" },
  { id: "fall3", name: "Fall Y3", year: 3, term: "Fall" },
  { id: "spring3", name: "Spr Y3", year: 3, term: "Spring" },
  { id: "fall4", name: "Fall Y4", year: 4, term: "Fall" },
  { id: "spring4", name: "Spr Y4", year: 4, term: "Spring" },
]

// Default empty plan
const EMPTY_PLAN = {
  fall1: [], spring1: [], fall2: [], spring2: [],
  fall3: [], spring3: [], fall4: [], spring4: [],
}

export default function App() {
  // Auth state
  const [user, setUserState] = useState(getUser())
  const [authMode, setAuthMode] = useState('login') // login, signup, forgot, reset, verify
  const [authForm, setAuthForm] = useState({ email: '', password: '', name: '', confirmPassword: '', major: 'CS', minor: '', concentration: '', startYear: new Date().getFullYear(), gradYear: new Date().getFullYear() + 4 })
  const [majorsList, setMajorsList] = useState([])
  const [minorsList, setMinorsList] = useState([])
  const [concentrationsList, setConcentrationsList] = useState([])
  const [authError, setAuthError] = useState(null)
  const [authSuccess, setAuthSuccess] = useState(null)
  const [authLoading, setAuthLoading] = useState(false)

  // Profile editing state
  const [profileForm, setProfileForm] = useState({ name: '', major: '', minor: '', concentration: '', startYear: '', gradYear: '' })
  const [profileConcentrationsList, setProfileConcentrationsList] = useState([])
  const [profileLoading, setProfileLoading] = useState(false)
  const [profileMessage, setProfileMessage] = useState(null)

  // Searchable dropdown state for signup
  const [majorSearch, setMajorSearch] = useState('')
  const [minorSearch, setMinorSearch] = useState('')
  const [concentrationSearch, setConcentrationSearch] = useState('')
  const [showMajorDropdown, setShowMajorDropdown] = useState(false)
  const [showMinorDropdown, setShowMinorDropdown] = useState(false)
  const [showConcentrationDropdown, setShowConcentrationDropdown] = useState(false)

  // Searchable dropdown state for profile
  const [profileMajorSearch, setProfileMajorSearch] = useState('')
  const [profileMinorSearch, setProfileMinorSearch] = useState('')
  const [profileConcentrationSearch, setProfileConcentrationSearch] = useState('')
  const [showProfileMajorDropdown, setShowProfileMajorDropdown] = useState(false)
  const [showProfileMinorDropdown, setShowProfileMinorDropdown] = useState(false)
  const [showProfileConcentrationDropdown, setShowProfileConcentrationDropdown] = useState(false)

  // Get URL params for token-based flows
  const urlParams = new URLSearchParams(window.location.search)
  const resetToken = urlParams.get('token')
  const isResetPage = window.location.pathname === '/reset-password'
  const isVerifyPage = window.location.pathname === '/verify-email'

  // App state
  const [currentView, setCurrentView] = useState('home')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [savedAudits, setSavedAudits] = useState([])

  // Courses state - loaded from backend
  const [allCourses, setAllCourses] = useState(DEFAULT_COURSES)
  const [coursesLoading, setCoursesLoading] = useState(true)

  // Planner state
  const [semesterPlan, setSemesterPlan] = useState(EMPTY_PLAN)
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [draggedCourse, setDraggedCourse] = useState(null)
  const [dragSource, setDragSource] = useState(null)
  const [aiAnalysis, setAiAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [sidebarTab, setSidebarTab] = useState('required')

  // Plans state
  const [savedPlans, setSavedPlans] = useState([])
  const [currentPlanId, setCurrentPlanId] = useState(null)
  const [currentPlanName, setCurrentPlanName] = useState('')
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [showLoadModal, setShowLoadModal] = useState(false)
  const [savePlanName, setSavePlanName] = useState('')
  const [plansLoading, setPlansLoading] = useState(false)
  const [exporting, setExporting] = useState(false)

  // Share state
  const [showShareModal, setShowShareModal] = useState(false)
  const [shareUrl, setShareUrl] = useState('')
  const [shareCopied, setShareCopied] = useState(false)

  // Shared plan view state
  const [sharedPlanData, setSharedPlanData] = useState(null)
  const [sharedPlanLoading, setSharedPlanLoading] = useState(false)

  // Course search/filter state
  const [courseSearch, setCourseSearch] = useState('')
  const [courseFilter, setCourseFilter] = useState({ category: '', difficulty: '', tags: '' })

  // Prereq visualization state
  const [showPrereqModal, setShowPrereqModal] = useState(false)
  const [prereqCourse, setPrereqCourse] = useState(null)

  // AI Preferences
  const [preferences, setPreferences] = useState({
    easiest: false,
    bestProfessors: true,
    leastWorkload: false,
    lateTimes: false,
    balanced: true,
  })

  // Auto-plan priority and career path
  const [planPriority, setPlanPriority] = useState('on_time')
  const [planCareerPath, setPlanCareerPath] = useState('')
  const [autoplanWarnings, setAutoplanWarnings] = useState([])

  // Get completed courses from DARS
  const completedCodes = useMemo(() => {
    return new Set(result?.completed?.map(c => c.code) || [])
  }, [result])

  const inProgressCodes = useMemo(() => {
    return new Set(result?.in_progress?.map(c => c.code) || [])
  }, [result])

  // All planned courses across semesters
  const allPlannedCourses = useMemo(() => {
    const planned = new Set()
    Object.values(semesterPlan).forEach(courses => {
      courses.forEach(c => planned.add(c))
    })
    return planned
  }, [semesterPlan])

  // Get courses taken before a semester
  const getCoursesBeforeSemester = useCallback((semesterId) => {
    const taken = new Set([...completedCodes, ...inProgressCodes])
    const semIndex = SEMESTERS.findIndex(s => s.id === semesterId)
    for (let i = 0; i < semIndex; i++) {
      const sem = SEMESTERS[i]
      ;(semesterPlan[sem.id] || []).forEach(c => taken.add(c))
    }
    return taken
  }, [semesterPlan, completedCodes, inProgressCodes])

  // Evaluate AND/OR prerequisite tree
  const evaluatePrereqTree = useCallback((node, takenSet) => {
    if (!node) return true
    if (node.type === 'COURSE') return takenSet.has(node.code)
    if (node.type === 'AND') return (node.requirements || []).every(r => evaluatePrereqTree(r, takenSet))
    if (node.type === 'OR') return (node.requirements || []).some(r => evaluatePrereqTree(r, takenSet))
    return true
  }, [])

  // Check if prereqs are met (supports AND/OR trees)
  const prereqsMet = useCallback((code, semesterId) => {
    const info = allCourses[code]
    if (!info) return true
    const taken = getCoursesBeforeSemester(semesterId)

    // Use structured prereqs if available
    if (info.prereqs_structured) {
      return evaluatePrereqTree(info.prereqs_structured, taken)
    }

    // Fallback to flat list (AND-all)
    return (info.prereqs || []).every(p => taken.has(p))
  }, [getCoursesBeforeSemester, evaluatePrereqTree])

  // Get semester credits
  const getSemesterCredits = useCallback((semesterId) => {
    return (semesterPlan[semesterId] || []).reduce((sum, code) => {
      return sum + (allCourses[code]?.credits || 3)
    }, 0)
  }, [semesterPlan])

  // DRAG AND DROP HANDLERS
  const handleDragStart = (e, code, source = 'library') => {
    // Set multiple data types for better compatibility
    e.dataTransfer.setData('text/plain', code)
    e.dataTransfer.setData('application/x-course', code)
    e.dataTransfer.effectAllowed = 'move'

    // Set drag image (optional visual feedback)
    if (e.target) {
      e.dataTransfer.setDragImage(e.target, 50, 20)
    }

    setDraggedCourse(code)
    setDragSource(source)

    // Add a class to body for global drag styling
    document.body.classList.add('dragging-course')
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e, targetSemester) => {
    e.preventDefault()
    e.stopPropagation()

    // Try multiple data types
    let code = e.dataTransfer.getData('application/x-course') || e.dataTransfer.getData('text/plain')

    // Fallback to tracked state if dataTransfer fails
    if (!code && draggedCourse) {
      code = draggedCourse
    }

    if (!code) {
      setDraggedCourse(null)
      setDragSource(null)
      document.body.classList.remove('dragging-course')
      return
    }

    setSemesterPlan(prev => {
      const newPlan = { ...prev }

      // Remove from source if it was from a semester (not library)
      if (dragSource && dragSource !== 'library') {
        newPlan[dragSource] = (prev[dragSource] || []).filter(c => c !== code)
      }

      // Add to target if not already there
      if (!newPlan[targetSemester]?.includes(code)) {
        newPlan[targetSemester] = [...(prev[targetSemester] || []), code]
      }

      return newPlan
    })

    setDraggedCourse(null)
    setDragSource(null)
    document.body.classList.remove('dragging-course')
  }

  const handleDragEnd = () => {
    setDraggedCourse(null)
    setDragSource(null)
    document.body.classList.remove('dragging-course')
  }

  // Remove course from semester
  const removeCourse = (code, semesterId) => {
    setSemesterPlan(prev => ({
      ...prev,
      [semesterId]: (prev[semesterId] || []).filter(c => c !== code)
    }))
  }

  // Add course by clicking
  const addCourseToSemester = (code, semesterId) => {
    if (allPlannedCourses.has(code)) return // Only prevent duplicates in planner
    setSemesterPlan(prev => ({
      ...prev,
      [semesterId]: [...(prev[semesterId] || []), code]
    }))
  }

  // Get courses by category (respects search filter)
  const coursesByCategory = useMemo(() => {
    const categories = {}

    // Apply search filter first
    let coursesToShow = Object.entries(allCourses)
    if (courseSearch) {
      const search = courseSearch.toLowerCase()
      coursesToShow = coursesToShow.filter(([code, info]) =>
        code.toLowerCase().includes(search) ||
        info.name?.toLowerCase().includes(search)
      )
    }

    coursesToShow.forEach(([code, info]) => {
      if (!categories[info.category]) categories[info.category] = []
      categories[info.category].push(code)
    })
    return categories
  }, [allCourses, courseSearch])

  // Generate optimal schedule - uses backend API with fallback to local algorithm
  const generateOptimalSchedule = async () => {
    setAnalyzing(true)
    setAutoplanWarnings([])

    try {
      // Try backend API first
      const res = await fetch(`${API}/auto-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(localStorage.getItem('token') ? { Authorization: `Bearer ${localStorage.getItem('token')}` } : {})
        },
        body: JSON.stringify({
          major: user?.major || 'CS',
          minor: user?.minor || null,
          concentration: user?.concentration || null,
          completed: [...completedCodes],
          in_progress: [...inProgressCodes],
          start_semester: 'fall1',
          remaining_semesters: 8,
          priority: planPriority,
          career_path: planCareerPath || null,
          preferences: {
            max_credits: preferences.balanced ? 15 : 18,
            balanced: preferences.balanced,
          }
        })
      })
      const data = await res.json()
      if (data.success && data.plan) {
        setSemesterPlan(data.plan)
        if (data.warnings && data.warnings.length > 0) {
          setAutoplanWarnings(data.warnings)
        }
        setAnalyzing(false)
        return
      }
    } catch (err) {
      console.log('Backend auto-plan unavailable, using local algorithm:', err.message)
    }

    // Fallback: local algorithm
    generateLocalSchedule()
    setAnalyzing(false)
  }

  // Local fallback auto-planner (works offline)
  const generateLocalSchedule = () => {
    const newPlan = { ...EMPTY_PLAN }
    const alreadyTaken = new Set([...completedCodes, ...inProgressCodes])

    // Get all courses to place, prioritizing required/core
    const toPlace = []
    const addedToPlace = new Set()

    Object.entries(allCourses).forEach(([code, info]) => {
      if (!alreadyTaken.has(code) && !addedToPlace.has(code)) {
        if (info.required || ['cs_core','math_core','math_discrete','stats','science'].includes(info.category)) {
          toPlace.push(code)
          addedToPlace.add(code)
        }
      }
    })

    const getEarliestSemester = (code, placedBySemester) => {
      const info = allCourses[code]
      if (!info) return 0
      const prereqs = info.prereqs || []
      if (prereqs.length === 0) return 0

      let minSemester = 0
      for (const prereq of prereqs) {
        if (alreadyTaken.has(prereq)) continue
        let prereqSem = -1
        for (let i = 0; i < SEMESTERS.length; i++) {
          if (placedBySemester[i]?.includes(prereq)) { prereqSem = i; break }
        }
        if (prereqSem === -1) return -1
        minSemester = Math.max(minSemester, prereqSem + 1)
      }
      return minSemester
    }

    const placedBySemester = SEMESTERS.map(() => [])
    const placed = new Set([...alreadyTaken])
    let changed = true, passes = 0

    while (changed && passes < 20) {
      changed = false
      passes++
      for (let i = toPlace.length - 1; i >= 0; i--) {
        const code = toPlace[i]
        if (placed.has(code)) { toPlace.splice(i, 1); continue }
        const earliestSem = getEarliestSemester(code, placedBySemester)
        if (earliestSem === -1) continue
        for (let semIdx = earliestSem; semIdx < SEMESTERS.length; semIdx++) {
          const semCredits = placedBySemester[semIdx].reduce((s, c) => s + (allCourses[c]?.credits || 3), 0)
          const maxCredits = preferences.balanced ? 15 : 18
          if (semCredits + (allCourses[code]?.credits || 3) <= maxCredits) {
            if (preferences.balanced) {
              const hardCount = placedBySemester[semIdx].filter(c => (allCourses[c]?.difficulty || 3) >= 4).length
              if ((allCourses[code]?.difficulty || 3) >= 4 && hardCount >= 2) continue
            }
            placedBySemester[semIdx].push(code)
            placed.add(code)
            toPlace.splice(i, 1)
            changed = true
            break
          }
        }
      }
    }

    SEMESTERS.forEach((sem, idx) => { newPlan[sem.id] = placedBySemester[idx] })
    setSemesterPlan(newPlan)
  }

  // Run AI Analysis
  const runAiAnalysis = async () => {
    setAnalyzing(true)
    try {
      const res = await fetch(`${API}/analyze-plan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
        },
        body: JSON.stringify({
          plan: semesterPlan,
          completed: [...completedCodes],
          in_progress: [...inProgressCodes],
          major: user?.major || 'CS',
          minor: user?.minor || null,
          preferences: preferences
        })
      })
      const data = await res.json()
      setAiAnalysis(data.analysis)
    } catch (err) {
      console.error('Analysis failed:', err)
      setAiAnalysis(generateLocalAnalysis())
    } finally {
      setAnalyzing(false)
    }
  }

  // Local analysis
  const generateLocalAnalysis = () => {
    const issues = []
    const suggestions = []
    const positives = []

    SEMESTERS.forEach(sem => {
      const courses = semesterPlan[sem.id] || []
      const credits = getSemesterCredits(sem.id)

      if (credits > 18) issues.push(`${sem.name}: ${credits} credits is too heavy`)
      if (credits >= 15 && credits <= 16) positives.push(`${sem.name}: Balanced ${credits} credits`)

      const hardCourses = courses.filter(c => (allCourses[c]?.difficulty || 3) >= 4)
      if (hardCourses.length >= 3) issues.push(`${sem.name}: ${hardCourses.length} difficult courses together`)

      courses.forEach(code => {
        if (!prereqsMet(code, sem.id)) {
          issues.push(`${code}: Missing prerequisites`)
        }
      })
    })

    // Professor suggestions
    if (preferences.bestProfessors) {
      Object.values(semesterPlan).flat().forEach(code => {
        const info = allCourses[code]
        const bestProf = info?.professors?.sort((a, b) => b.rating - a.rating)[0]
        if (bestProf && bestProf.rating >= 4.3) {
          positives.push(`${code}: Great professor option (${bestProf.name}, ${bestProf.rating}★)`)
        }
      })
    }

    if (!allPlannedCourses.has('CS 4604') && !completedCodes.has('CS 4604')) {
      suggestions.push('Add CS 4604 (Databases) - essential for industry, easy elective')
    }
    if (!allPlannedCourses.has('CS 4804') && !completedCodes.has('CS 4804')) {
      suggestions.push('Add CS 4804 (AI) - hot field, good professors')
    }

    return {
      overallScore: Math.max(0, Math.min(100, 100 - issues.length * 12 + positives.length * 5)),
      issues,
      suggestions,
      positives
    }
  }

  // Handle URL-based auth flows (verify email, reset password)
  useEffect(() => {
    const handleUrlAuth = async () => {
      if (isVerifyPage && resetToken) {
        setAuthMode('verify')
        setAuthLoading(true)
        try {
          const res = await fetch(`${API}/auth/verify-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: resetToken })
          })
          const data = await res.json()
          if (res.ok) {
            setAuthSuccess('Email verified successfully! You can now log in.')
            // Update user state if logged in
            if (user) {
              const updatedUser = { ...user, email_verified: true }
              setUserStorage(updatedUser)
              setUserState(updatedUser)
            }
          } else {
            setAuthError(data.detail || 'Verification failed')
          }
        } catch (err) {
          setAuthError('Verification failed. Please try again.')
        } finally {
          setAuthLoading(false)
        }
        // Clean URL
        window.history.replaceState({}, '', '/')
      } else if (isResetPage && resetToken) {
        setAuthMode('reset')
      }
    }
    handleUrlAuth()
  }, [])

  // Load courses from backend API
  useEffect(() => {
    const loadCourses = async () => {
      try {
        const res = await fetch(`${API}/courses`)
        if (res.ok) {
          const data = await res.json()
          // Convert array to object keyed by code
          const coursesObj = {}
          data.courses.forEach(course => {
            coursesObj[course.code] = {
              name: course.name,
              prereqs: course.prereqs || [],
              credits: course.credits || 3,
              category: course.category || '',
              difficulty: course.difficulty || 3,
              workload: course.workload || 3,
              required: (course.required_for || []).includes('cs_major'),
              professors: course.professors || [],
              timeSlots: course.typically_offered || [],
              tags: course.tags || [],
              description: course.description || ''
            }
          })
          if (Object.keys(coursesObj).length > 0) {
            setAllCourses(prev => ({ ...prev, ...coursesObj }))
          }
          console.log(`Loaded ${data.total} courses from API`)
        }
      } catch (err) {
        console.log('Using default courses (API not available)')
      } finally {
        setCoursesLoading(false)
      }
    }
    loadCourses()
  }, [])

  // Load majors list for signup
  useEffect(() => {
    const loadMajors = async () => {
      try {
        const res = await fetch(`${API}/majors`)
        if (res.ok) {
          const data = await res.json()
          setMajorsList(data.majors || [])
        }
      } catch (err) {
        console.log('Could not load majors list')
        // Fallback majors
        setMajorsList([
          { code: 'CS', name: 'Computer Science', college: 'Engineering' },
          { code: 'ECE', name: 'Electrical and Computer Engineering', college: 'Engineering' },
          { code: 'ME', name: 'Mechanical Engineering', college: 'Engineering' },
          { code: 'CMDA', name: 'Computational Modeling and Data Analytics', college: 'Science' },
          { code: 'BIOL', name: 'Biological Sciences', college: 'Science' },
          { code: 'BUS', name: 'Business', college: 'Pamplin' },
          { code: 'OTHER', name: 'Other / Undeclared', college: 'General' }
        ])
      }
    }
    loadMajors()
  }, [])

  // Load minors list for signup
  useEffect(() => {
    const loadMinors = async () => {
      try {
        const res = await fetch(`${API}/minors`)
        if (res.ok) {
          const data = await res.json()
          setMinorsList(data.minors || [])
        }
      } catch (err) {
        console.log('Could not load minors list')
        // Fallback minors
        setMinorsList([
          { code: 'NONE', name: 'No Minor' },
          { code: 'CS', name: 'Computer Science' },
          { code: 'MATH', name: 'Mathematics' },
          { code: 'STAT', name: 'Statistics' }
        ])
      }
    }
    loadMinors()
  }, [])

  // Load concentrations when major changes (for signup form)
  useEffect(() => {
    const loadConcentrations = async () => {
      if (!authForm.major) {
        setConcentrationsList([])
        return
      }
      try {
        const res = await fetch(`${API}/concentrations?major=${authForm.major}`)
        if (res.ok) {
          const data = await res.json()
          setConcentrationsList(data.concentrations || [])
          // Clear concentration if it doesn't exist in new list
          if (data.concentrations?.length === 0 || !data.concentrations?.find(c => c.code === authForm.concentration)) {
            setAuthForm(prev => ({ ...prev, concentration: '' }))
          }
        }
      } catch (err) {
        console.log('Could not load concentrations')
        setConcentrationsList([])
      }
    }
    loadConcentrations()
  }, [authForm.major])

  // Load concentrations when major changes (for profile form)
  useEffect(() => {
    const loadProfileConcentrations = async () => {
      if (!profileForm.major) {
        setProfileConcentrationsList([])
        return
      }
      try {
        const res = await fetch(`${API}/concentrations?major=${profileForm.major}`)
        if (res.ok) {
          const data = await res.json()
          setProfileConcentrationsList(data.concentrations || [])
        }
      } catch (err) {
        console.log('Could not load profile concentrations')
        setProfileConcentrationsList([])
      }
    }
    loadProfileConcentrations()
  }, [profileForm.major])

  // Auth handlers
  useEffect(() => {
    if (user) fetchSavedAudits()
  }, [user])

  // Initialize profile form when viewing profile page
  useEffect(() => {
    if (currentView === 'profile' && user) {
      initProfileForm()
    }
  }, [currentView, user])

  const fetchSavedAudits = async () => {
    try {
      const res = await fetch(`${API}/my-audits`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      if (res.ok) {
        const data = await res.json()
        setSavedAudits(data.audits || [])
        if (data.audits?.length > 0) {
          const latest = data.audits[0]
          setResult({
            major: latest.major,
            completed: latest.completed,
            in_progress: latest.in_progress,
            roadmap: latest.roadmap
          })
        }
      }
    } catch (err) {
      console.error('Failed to fetch audits:', err)
    }
  }

  // Fetch saved plans
  const fetchSavedPlans = async () => {
    try {
      const res = await fetch(`${API}/plans`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      if (res.ok) {
        const data = await res.json()
        setSavedPlans(data.plans || [])
        // Load default plan if exists
        const defaultPlan = data.plans?.find(p => p.is_default)
        if (defaultPlan) {
          setSemesterPlan(defaultPlan.plan_data)
          setCurrentPlanId(defaultPlan.id)
          setCurrentPlanName(defaultPlan.name)
        }
      }
    } catch (err) {
      console.error('Failed to fetch plans:', err)
    }
  }

  // Load plans when user logs in
  useEffect(() => {
    if (user) fetchSavedPlans()
  }, [user])

  // Save plan
  const handleSavePlan = async (asNew = false) => {
    if (!savePlanName.trim()) return
    setPlansLoading(true)

    try {
      if (currentPlanId && !asNew) {
        // Update existing plan
        const res = await fetch(`${API}/plans/${currentPlanId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`
          },
          body: JSON.stringify({ name: savePlanName, plan_data: semesterPlan })
        })
        if (!res.ok) throw new Error('Failed to update plan')
        setCurrentPlanName(savePlanName)
      } else {
        // Create new plan
        const res = await fetch(`${API}/plans`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`
          },
          body: JSON.stringify({ name: savePlanName, plan_data: semesterPlan, is_default: savedPlans.length === 0 })
        })
        if (!res.ok) throw new Error('Failed to save plan')
        const data = await res.json()
        setCurrentPlanId(data.plan.id)
        setCurrentPlanName(savePlanName)
      }
      await fetchSavedPlans()
      setShowSaveModal(false)
      setSavePlanName('')
    } catch (err) {
      console.error('Failed to save plan:', err)
      alert('Failed to save plan')
    } finally {
      setPlansLoading(false)
    }
  }

  // Load a plan
  const handleLoadPlan = async (plan) => {
    setSemesterPlan(plan.plan_data)
    setCurrentPlanId(plan.id)
    setCurrentPlanName(plan.name)
    setShowLoadModal(false)
  }

  // Delete a plan
  const handleDeletePlan = async (planId) => {
    if (!confirm('Delete this plan?')) return
    try {
      const res = await fetch(`${API}/plans/${planId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` }
      })
      if (!res.ok) throw new Error('Failed to delete')
      if (currentPlanId === planId) {
        setCurrentPlanId(null)
        setCurrentPlanName('')
      }
      await fetchSavedPlans()
    } catch (err) {
      console.error('Failed to delete plan:', err)
    }
  }

  // Export to PDF
  const exportToPDF = async () => {
    setExporting(true)
    try {
      const html2canvas = (await import('html2canvas')).default
      const jsPDF = (await import('jspdf')).default

      const planElement = document.getElementById('graduation-plan')
      if (!planElement) return

      const canvas = await html2canvas(planElement, { scale: 2, backgroundColor: '#f8fafc' })
      const imgData = canvas.toDataURL('image/png')

      const pdf = new jsPDF('l', 'mm', 'a4')
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = pdf.internal.pageSize.getHeight()

      const imgWidth = canvas.width
      const imgHeight = canvas.height
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)

      const imgX = (pdfWidth - imgWidth * ratio) / 2
      const imgY = 10

      pdf.setFontSize(16)
      pdf.text(`VT Graduation Plan${currentPlanName ? ': ' + currentPlanName : ''}`, pdfWidth / 2, 10, { align: 'center' })
      pdf.addImage(imgData, 'PNG', imgX, imgY + 5, imgWidth * ratio, imgHeight * ratio)
      pdf.save(`graduation-plan${currentPlanName ? '-' + currentPlanName.replace(/\s+/g, '-') : ''}.pdf`)
    } catch (err) {
      console.error('Export failed:', err)
      alert('Failed to export PDF')
    } finally {
      setExporting(false)
    }
  }

  // Export to Image
  const exportToImage = async () => {
    setExporting(true)
    try {
      const html2canvas = (await import('html2canvas')).default

      const planElement = document.getElementById('graduation-plan')
      if (!planElement) return

      const canvas = await html2canvas(planElement, { scale: 2, backgroundColor: '#f8fafc' })
      const link = document.createElement('a')
      link.download = `graduation-plan${currentPlanName ? '-' + currentPlanName.replace(/\s+/g, '-') : ''}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } catch (err) {
      console.error('Export failed:', err)
      alert('Failed to export image')
    } finally {
      setExporting(false)
    }
  }

  // Share plan
  const handleSharePlan = async () => {
    if (!currentPlanId) {
      alert('Please save your plan first before sharing')
      return
    }

    try {
      const res = await fetch(`${API}/share`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ plan_id: currentPlanId })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to create share link')

      setShareUrl(data.share_url)
      setShowShareModal(true)
      setShareCopied(false)
    } catch (err) {
      console.error('Share failed:', err)
      alert('Failed to create share link')
    }
  }

  const copyShareLink = () => {
    navigator.clipboard.writeText(shareUrl)
    setShareCopied(true)
    setTimeout(() => setShareCopied(false), 2000)
  }

  // Check for shared plan URL
  useEffect(() => {
    const path = window.location.pathname
    if (path.startsWith('/shared/')) {
      const token = path.replace('/shared/', '')
      loadSharedPlan(token)
    }
  }, [])

  const loadSharedPlan = async (token) => {
    setSharedPlanLoading(true)
    try {
      const res = await fetch(`${API}/shared/${token}`)
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Failed to load shared plan')
      }
      const data = await res.json()
      setSharedPlanData(data)
    } catch (err) {
      console.error('Failed to load shared plan:', err)
      setSharedPlanData({ error: err.message })
    } finally {
      setSharedPlanLoading(false)
    }
  }

  // Calculate degree progress
  const degreeProgress = useMemo(() => {
    const completed = new Set([...completedCodes])
    const planned = new Set([...allPlannedCourses])
    const all = new Set([...completed, ...planned])

    const progress = {}
    let totalRequired = 0
    let totalCompleted = 0
    let totalPlanned = 0

    // CS Core
    const csCore = DEGREE_REQUIREMENTS.cs_core.required
    const csCoreCompleted = csCore.filter(c => completed.has(c))
    const csCorePlanned = csCore.filter(c => planned.has(c) && !completed.has(c))
    progress.cs_core = {
      name: "CS Core",
      required: csCore,
      completed: csCoreCompleted,
      planned: csCorePlanned,
      remaining: csCore.filter(c => !all.has(c)),
      percent: Math.round((csCoreCompleted.length / csCore.length) * 100),
      percentWithPlanned: Math.round(((csCoreCompleted.length + csCorePlanned.length) / csCore.length) * 100),
      color: "blue"
    }
    totalRequired += csCore.length
    totalCompleted += csCoreCompleted.length
    totalPlanned += csCorePlanned.length

    // CS 4104 + Systems elective
    const cs4104Done = completed.has("CS 4104") || planned.has("CS 4104")
    const systemsOptions = ["CS 4114", "CS 4254", "CS 4284"]
    const systemsCompleted = systemsOptions.filter(c => completed.has(c))
    const systemsPlanned = systemsOptions.filter(c => planned.has(c) && !completed.has(c))
    progress.cs_systems = {
      name: "Theory & Systems",
      required: ["CS 4104"],
      chooseFrom: systemsOptions,
      completed: [...(completed.has("CS 4104") ? ["CS 4104"] : []), ...systemsCompleted],
      planned: [...(planned.has("CS 4104") && !completed.has("CS 4104") ? ["CS 4104"] : []), ...systemsPlanned],
      needsCS4104: !cs4104Done,
      needsSystemsElective: systemsCompleted.length === 0 && systemsPlanned.length === 0,
      percent: Math.round(((completed.has("CS 4104") ? 1 : 0) + Math.min(1, systemsCompleted.length)) / 2 * 100),
      color: "indigo"
    }
    totalRequired += 2
    totalCompleted += (completed.has("CS 4104") ? 1 : 0) + Math.min(1, systemsCompleted.length)
    totalPlanned += (planned.has("CS 4104") && !completed.has("CS 4104") ? 1 : 0) + (systemsCompleted.length === 0 ? Math.min(1, systemsPlanned.length) : 0)

    // Math Core
    const mathCore = DEGREE_REQUIREMENTS.math_core.required
    const mathCompleted = mathCore.filter(c => completed.has(c))
    const mathPlanned = mathCore.filter(c => planned.has(c) && !completed.has(c))
    progress.math_core = {
      name: "Math Core",
      required: mathCore,
      completed: mathCompleted,
      planned: mathPlanned,
      remaining: mathCore.filter(c => !all.has(c)),
      percent: Math.round((mathCompleted.length / mathCore.length) * 100),
      color: "green"
    }
    totalRequired += mathCore.length
    totalCompleted += mathCompleted.length
    totalPlanned += mathPlanned.length

    // Stats
    const statsOptions = DEGREE_REQUIREMENTS.stats.from
    const statsCompleted = statsOptions.filter(c => completed.has(c))
    const statsPlanned = statsOptions.filter(c => planned.has(c) && !completed.has(c))
    progress.stats = {
      name: "Statistics",
      chooseFrom: statsOptions,
      completed: statsCompleted,
      planned: statsPlanned,
      percent: statsCompleted.length > 0 ? 100 : 0,
      color: "teal"
    }
    totalRequired += 1
    totalCompleted += Math.min(1, statsCompleted.length)
    totalPlanned += statsCompleted.length === 0 ? Math.min(1, statsPlanned.length) : 0

    // Science
    const scienceReq = DEGREE_REQUIREMENTS.science.required
    const scienceCompleted = scienceReq.filter(c => completed.has(c))
    const sciencePlanned = scienceReq.filter(c => planned.has(c) && !completed.has(c))
    progress.science = {
      name: "Science",
      required: scienceReq,
      completed: scienceCompleted,
      planned: sciencePlanned,
      remaining: scienceReq.filter(c => !all.has(c)),
      percent: Math.round((scienceCompleted.length / scienceReq.length) * 100),
      color: "emerald"
    }
    totalRequired += scienceReq.length
    totalCompleted += scienceCompleted.length
    totalPlanned += sciencePlanned.length

    // CS Electives (need 3)
    const csElectives = Object.entries(allCourses)
      .filter(([code, info]) => info.category === 'cs_elective' || (code.startsWith('CS') && parseInt(code.split(' ')[1]) >= 3000))
      .map(([code]) => code)
    const csElecCompleted = csElectives.filter(c => completed.has(c))
    const csElecPlanned = csElectives.filter(c => planned.has(c) && !completed.has(c))
    progress.cs_electives = {
      name: "CS Electives",
      minCourses: 3,
      completed: csElecCompleted,
      planned: csElecPlanned,
      percent: Math.round((Math.min(3, csElecCompleted.length) / 3) * 100),
      color: "purple"
    }
    totalRequired += 3
    totalCompleted += Math.min(3, csElecCompleted.length)
    totalPlanned += Math.min(3 - csElecCompleted.length, csElecPlanned.length)

    // Capstone
    const capstoneOptions = DEGREE_REQUIREMENTS.capstone.from
    const capstoneCompleted = capstoneOptions.filter(c => completed.has(c))
    const capstonePlanned = capstoneOptions.filter(c => planned.has(c) && !completed.has(c))
    progress.capstone = {
      name: "Capstone",
      chooseFrom: capstoneOptions,
      completed: capstoneCompleted,
      planned: capstonePlanned,
      percent: capstoneCompleted.length > 0 ? 100 : 0,
      color: "pink"
    }
    totalRequired += 1
    totalCompleted += Math.min(1, capstoneCompleted.length)
    totalPlanned += capstoneCompleted.length === 0 ? Math.min(1, capstonePlanned.length) : 0

    // Overall
    const overallPercent = Math.round((totalCompleted / totalRequired) * 100)
    const overallWithPlanned = Math.round(((totalCompleted + totalPlanned) / totalRequired) * 100)

    // Total credits
    const completedCredits = [...completed].reduce((sum, c) => sum + (allCourses[c]?.credits || 3), 0)
    const plannedCredits = [...planned].reduce((sum, c) => sum + (allCourses[c]?.credits || 3), 0)

    return {
      categories: progress,
      overall: {
        percent: overallPercent,
        percentWithPlanned: overallWithPlanned,
        completedCourses: totalCompleted,
        plannedCourses: totalPlanned,
        totalRequired: totalRequired,
        completedCredits,
        plannedCredits,
        totalCredits: 120,
        remainingCredits: Math.max(0, 120 - completedCredits - plannedCredits)
      }
    }
  }, [completedCodes, allPlannedCourses, allCourses])

  // Build prerequisite chain for visualization
  const getPrereqChain = useCallback((code, visited = new Set()) => {
    if (visited.has(code)) return { code, prereqs: [], circular: true }
    visited.add(code)

    const info = allCourses[code]
    if (!info) return { code, prereqs: [] }

    const prereqs = (info.prereqs || []).map(p => getPrereqChain(p, new Set(visited)))
    return { code, name: info.name, prereqs }
  }, [allCourses])

  // Get courses that require this course
  const getCoursesRequiring = useCallback((code) => {
    return Object.entries(allCourses)
      .filter(([, info]) => info.prereqs?.includes(code))
      .map(([c, info]) => ({ code: c, name: info.name }))
  }, [allCourses])

  // Filtered courses for search
  const filteredCourses = useMemo(() => {
    let courses = Object.entries(allCourses)

    if (courseSearch) {
      const search = courseSearch.toLowerCase()
      courses = courses.filter(([code, info]) =>
        code.toLowerCase().includes(search) ||
        info.name?.toLowerCase().includes(search) ||
        info.tags?.some(t => t.toLowerCase().includes(search))
      )
    }

    if (courseFilter.category) {
      courses = courses.filter(([, info]) => info.category === courseFilter.category)
    }

    if (courseFilter.difficulty) {
      courses = courses.filter(([, info]) => info.difficulty === parseInt(courseFilter.difficulty))
    }

    return Object.fromEntries(courses)
  }, [allCourses, courseSearch, courseFilter])

  const handleAuth = async (e) => {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError(null)
    setAuthSuccess(null)

    try {
      if (authMode === 'forgot') {
        // Forgot password - request reset email
        const res = await fetch(`${API}/auth/forgot-password`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authForm.email })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to send reset email')
        setAuthSuccess('Password reset email sent! Check your inbox.')
        return
      }

      if (authMode === 'reset') {
        // Reset password with token
        if (authForm.password !== authForm.confirmPassword) {
          throw new Error('Passwords do not match')
        }
        const res = await fetch(`${API}/auth/reset-password`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: resetToken, new_password: authForm.password })
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || 'Failed to reset password')
        setAuthSuccess('Password reset successfully! You can now log in.')
        setAuthMode('login')
        window.history.replaceState({}, '', '/')
        return
      }

      // Login or signup
      const endpoint = authMode === 'login' ? '/auth/login' : '/auth/signup'
      const body = authMode === 'login'
        ? { email: authForm.email, password: authForm.password }
        : {
            email: authForm.email,
            password: authForm.password,
            name: authForm.name,
            major: authForm.major,
            minor: authForm.minor || null,
            concentration: authForm.concentration || null,
            start_year: authForm.startYear,
            grad_year: authForm.gradYear
          }

      const res = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Authentication failed')

      setToken(data.token)
      setUserStorage(data.user)
      setUserState(data.user)
      setAuthForm({ email: '', password: '', name: '', confirmPassword: '', major: 'CS', minor: '', concentration: '', startYear: new Date().getFullYear(), gradYear: new Date().getFullYear() + 4 })

      // Show verification message for new signups
      if (authMode === 'signup') {
        setAuthSuccess('Account created! Please check your email to verify.')
      }
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleResendVerification = async () => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const res = await fetch(`${API}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user?.email || authForm.email })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to resend verification')
      setAuthSuccess('Verification email sent! Check your inbox.')
    } catch (err) {
      setAuthError(err.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    removeToken()
    removeUser()
    setUserState(null)
    setResult(null)
    setSavedAudits([])
    setCurrentView('home')
  }

  // Initialize profile form when viewing profile
  const initProfileForm = () => {
    if (user) {
      setProfileForm({
        name: user.name || '',
        major: user.major || 'CS',
        minor: user.minor || '',
        concentration: user.concentration || '',
        startYear: user.start_year || user.startYear || new Date().getFullYear(),
        gradYear: user.grad_year || user.gradYear || new Date().getFullYear() + 4
      })
      setProfileMessage(null)
    }
  }

  // Handle profile update
  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setProfileLoading(true)
    setProfileMessage(null)

    try {
      const res = await fetch(`${API}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          name: profileForm.name,
          major: profileForm.major,
          minor: profileForm.minor || null,
          concentration: profileForm.concentration || null,
          start_year: parseInt(profileForm.startYear),
          grad_year: parseInt(profileForm.gradYear)
        })
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Failed to update profile')

      // Update local user state
      const updatedUser = {
        ...user,
        name: profileForm.name,
        major: profileForm.major,
        minor: profileForm.minor || null,
        concentration: profileForm.concentration || null,
        start_year: parseInt(profileForm.startYear),
        grad_year: parseInt(profileForm.gradYear)
      }
      setUserStorage(updatedUser)
      setUserState(updatedUser)
      setProfileMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (err) {
      setProfileMessage({ type: 'error', text: err.message })
    } finally {
      setProfileLoading(false)
    }
  }

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const headers = {}
      if (getToken()) headers.Authorization = `Bearer ${getToken()}`

      const res = await fetch(`${API}/analyze`, {
        method: 'POST',
        headers,
        body: formData,
      })

      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      setResult(data.data)
      setCurrentView('planner')
      setFile(null)
      if (user) fetchSavedAudits()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // =====================
  // LANDING PAGE
  // =====================

  // Add global drag styles and dark mode
  useEffect(() => {
    const style = document.createElement('style')
    style.textContent = `
      .dragging-course * { cursor: grabbing !important; }
      [draggable="true"]:hover { transform: scale(1.02); }
      [draggable="true"]:active { transform: scale(0.98); }
      .dark { color-scheme: dark; }
      .dark body { background: #0f172a; color: #e2e8f0; }
    `
    document.head.appendChild(style)
    return () => document.head.removeChild(style)
  }, [])

  // Shared Plan View (public, no auth required)
  if (sharedPlanData || sharedPlanLoading) {
    return (
      <div className="min-h-screen bg-[#FDFCF8]">
        <nav className="bg-white border-b border-slate-900 px-6 py-4">
          <div className="flex justify-between items-center max-w-6xl mx-auto">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-slate-900 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
                </svg>
              </div>
              <span className="font-serif font-medium text-slate-900">VT Optimizer</span>
            </div>
            <span className="text-xs uppercase tracking-widest text-slate-500">Shared Plan</span>
          </div>
        </nav>

        <div className="max-w-6xl mx-auto p-8">
          {sharedPlanLoading ? (
            <div className="text-center py-20">
              <div className="editorial-spinner mx-auto mb-4"></div>
              <p className="text-slate-500">Loading shared plan...</p>
            </div>
          ) : sharedPlanData?.error ? (
            <div className="text-center py-20">
              <h2 className="text-2xl font-serif mb-3 text-slate-800">Plan Not Found</h2>
              <p className="text-slate-500 mb-6">{sharedPlanData.error}</p>
              <a href="/" className="px-6 py-3 bg-slate-900 text-white font-serif hover:bg-slate-800 transition-colors">Go Home</a>
            </div>
          ) : (
            <>
              <div className="text-center mb-10">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Shared Plan</p>
                <h1 className="text-3xl font-serif text-slate-900 mb-2">
                  {sharedPlanData.student_name}'s Graduation Plan
                </h1>
                <div className="w-16 h-px bg-slate-900 mx-auto my-4"></div>
                <p className="text-slate-600">{sharedPlanData.plan_name}</p>
                <p className="text-xs mt-2 text-slate-400">
                  Viewed {sharedPlanData.view_count} times
                </p>
              </div>

              <div className="grid grid-cols-4 gap-4">
                {SEMESTERS.map(sem => {
                  const courses = sharedPlanData.plan_data?.[sem.id] || []
                  return (
                    <div key={sem.id} className="bg-white border border-slate-900 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] p-4">
                      <h3 className="text-sm font-serif font-medium mb-3 pb-2 border-b border-slate-200 text-slate-800">{sem.name}</h3>
                      <div className="space-y-2">
                        {courses.map(code => (
                          <div key={code} className="px-3 py-2 text-sm bg-slate-50 border border-slate-300">
                            <div className="font-medium text-slate-800">{code}</div>
                            <div className="text-xs text-slate-500">
                              {allCourses[code]?.name || ''}
                            </div>
                          </div>
                        ))}
                        {courses.length === 0 && (
                          <p className="text-xs text-slate-400 text-center py-4">No courses planned</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-[#FDFCF8]">
        <div className="text-center max-w-md w-full mx-auto">
          {/* Editorial Logo */}
          <div className="w-12 h-12 mx-auto mb-6 bg-slate-900 flex items-center justify-center">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
            </svg>
          </div>

          <h1 className="text-4xl font-serif font-medium mb-3 text-slate-900">
            VT Optimizer
          </h1>
          <div className="w-16 h-px bg-slate-900 mx-auto mb-3"></div>
          <p className="text-slate-600 mb-8 font-light">Advising, <em className="font-serif">made better.</em></p>

          <div className="bg-white border border-slate-900 p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
            {/* Success Message */}
            {authSuccess && (
              <div className="mb-4 p-3 bg-green-50 border border-green-600 text-green-700 text-sm">
                {authSuccess}
              </div>
            )}

            {/* Verify Email Mode - Show result */}
            {authMode === 'verify' && (
              <div className="text-center py-4">
                {authLoading ? (
                  <div className="text-slate-500">Verifying your email...</div>
                ) : authError ? (
                  <div>
                    <div className="text-red-600 mb-3">{authError}</div>
                    <button onClick={() => { setAuthMode('login'); setAuthError(null) }}
                      className="text-slate-600 text-sm underline underline-offset-4 hover:text-slate-900">Back to login</button>
                  </div>
                ) : (
                  <div>
                    <div className="text-green-700 text-lg font-serif mb-4">Email verified!</div>
                    <button onClick={() => { setAuthMode('login'); setAuthSuccess(null) }}
                      className="px-6 py-3 bg-slate-900 text-white font-serif hover:bg-slate-800 transition-colors">
                      Log In
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Reset Password Mode */}
            {authMode === 'reset' && (
              <form onSubmit={handleAuth} className="space-y-5">
                <h2 className="text-xl font-serif text-slate-900 mb-1">Reset Password</h2>
                <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">Enter your new password below</p>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">New Password</label>
                  <input type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="Enter new password" required minLength={6} />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Confirm Password</label>
                  <input type="password" value={authForm.confirmPassword} onChange={(e) => setAuthForm({ ...authForm, confirmPassword: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="Confirm new password" required minLength={6} />
                </div>
                {authError && <p className="text-red-600 text-xs">{authError}</p>}
                <button type="submit" className="w-full py-3 bg-slate-900 text-white font-serif text-base hover:bg-slate-800 transition-colors mt-2" disabled={authLoading}>
                  {authLoading ? 'Please wait...' : 'Reset Password'}
                </button>
                <p className="text-center text-slate-500 text-xs mt-4">
                  <button type="button" onClick={() => { setAuthMode('login'); window.history.replaceState({}, '', '/') }} className="text-slate-600 underline underline-offset-4 hover:text-slate-900">Back to login</button>
                </p>
              </form>
            )}

            {/* Forgot Password Mode */}
            {authMode === 'forgot' && (
              <form onSubmit={handleAuth} className="space-y-5">
                <h2 className="text-xl font-serif text-slate-900 mb-1">Forgot Password?</h2>
                <p className="text-xs text-slate-500 uppercase tracking-widest mb-4">We'll send you a reset link</p>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Email Address</label>
                  <input type="email" value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="you@vt.edu" required />
                </div>
                {authError && <p className="text-red-600 text-xs">{authError}</p>}
                <button type="submit" className="w-full py-3 bg-slate-900 text-white font-serif text-base hover:bg-slate-800 transition-colors mt-2" disabled={authLoading}>
                  {authLoading ? 'Please wait...' : 'Send Reset Link'}
                </button>
                <p className="text-center text-slate-500 text-xs mt-4">
                  <button type="button" onClick={() => setAuthMode('login')} className="text-slate-600 underline underline-offset-4 hover:text-slate-900">Back to login</button>
                </p>
              </form>
            )}

            {/* Login Mode */}
            {authMode === 'login' && (
              <form onSubmit={handleAuth} className="space-y-5">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Email</label>
                  <input type="email" value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="you@vt.edu" required />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Password</label>
                  <input type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="Enter password" required minLength={6} />
                </div>
                {authError && <p className="text-red-600 text-xs">{authError}</p>}
                <button type="submit" className="w-full py-3 bg-slate-900 text-white font-serif text-base hover:bg-slate-800 transition-colors mt-2" disabled={authLoading}>
                  {authLoading ? 'Please wait...' : 'Log In'}
                </button>
                <div className="flex justify-between text-xs mt-4 pt-4 border-t border-slate-200">
                  <button type="button" onClick={() => setAuthMode('forgot')} className="text-slate-500 hover:text-slate-900 underline underline-offset-4">Forgot password?</button>
                  <span className="text-slate-500">New here? <button type="button" onClick={() => setAuthMode('signup')} className="text-slate-900 font-medium underline underline-offset-4">Sign up</button></span>
                </div>
              </form>
            )}

            {/* Signup Mode */}
            {authMode === 'signup' && (
              <form onSubmit={handleAuth} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Full Name</label>
                  <input type="text" value={authForm.name} onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="Your name" required />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Email</label>
                  <input type="email" value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="you@vt.edu" required />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Password</label>
                  <input type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base" placeholder="Create password" required minLength={6} />
                </div>

                {/* Major Selection - Searchable */}
                <div className="relative">
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Major <span className="font-normal normal-case">({majorsList.length})</span></label>
                  <input
                    type="text"
                    value={majorSearch || (majorsList.find(m => m.code === authForm.major)?.name || '')}
                    onChange={(e) => {
                      setMajorSearch(e.target.value)
                      setShowMajorDropdown(true)
                    }}
                    onFocus={() => setShowMajorDropdown(true)}
                    placeholder="Search majors..."
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                  />
                  {showMajorDropdown && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                      {majorsList
                        .filter(m =>
                          !majorSearch ||
                          m.name.toLowerCase().includes(majorSearch.toLowerCase()) ||
                          m.code.toLowerCase().includes(majorSearch.toLowerCase()) ||
                          m.college.toLowerCase().includes(majorSearch.toLowerCase())
                        )
                        .map(m => (
                          <button
                            key={m.code}
                            type="button"
                            onClick={() => {
                              setAuthForm({ ...authForm, major: m.code, concentration: '' })
                              setMajorSearch('')
                              setShowMajorDropdown(false)
                            }}
                            className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${authForm.major === m.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                          >
                            <div className="font-medium">{m.name}</div>
                            <div className={`text-xs ${authForm.major === m.code ? 'text-slate-300' : 'text-slate-400'}`}>{m.college} • {m.code}</div>
                          </button>
                        ))
                      }
                      {majorsList.filter(m =>
                        !majorSearch ||
                        m.name.toLowerCase().includes(majorSearch.toLowerCase()) ||
                        m.code.toLowerCase().includes(majorSearch.toLowerCase())
                      ).length === 0 && (
                        <div className="px-4 py-3 text-sm text-slate-400 text-center">No majors found</div>
                      )}
                    </div>
                  )}
                  {showMajorDropdown && (
                    <div className="fixed inset-0 z-40" onClick={() => setShowMajorDropdown(false)} />
                  )}
                </div>

                {/* Minor Selection - Searchable (Optional) */}
                <div className="relative">
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Minor <span className="font-normal normal-case">(Optional)</span></label>
                  <input
                    type="text"
                    value={minorSearch || (authForm.minor ? (minorsList.find(m => m.code === authForm.minor)?.name || '') : '')}
                    onChange={(e) => {
                      setMinorSearch(e.target.value)
                      setShowMinorDropdown(true)
                    }}
                    onFocus={() => setShowMinorDropdown(true)}
                    placeholder="Search minors..."
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                  />
                  {showMinorDropdown && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                      <button
                        type="button"
                        onClick={() => {
                          setAuthForm({ ...authForm, minor: '' })
                          setMinorSearch('')
                          setShowMinorDropdown(false)
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${!authForm.minor ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                      >
                        <div className="font-medium">No Minor</div>
                      </button>
                      {minorsList
                        .filter(m => m.code !== 'NONE')
                        .filter(m =>
                          !minorSearch ||
                          m.name.toLowerCase().includes(minorSearch.toLowerCase()) ||
                          m.code.toLowerCase().includes(minorSearch.toLowerCase())
                        )
                        .map(m => (
                          <button
                            key={m.code}
                            type="button"
                            onClick={() => {
                              setAuthForm({ ...authForm, minor: m.code })
                              setMinorSearch('')
                              setShowMinorDropdown(false)
                            }}
                            className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${authForm.minor === m.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                          >
                            <div className="font-medium">{m.name}</div>
                            <div className={`text-xs ${authForm.minor === m.code ? 'text-slate-300' : 'text-slate-400'}`}>{m.code}</div>
                          </button>
                        ))
                      }
                      {minorsList.filter(m =>
                        m.code !== 'NONE' && (!minorSearch ||
                        m.name.toLowerCase().includes(minorSearch.toLowerCase()) ||
                        m.code.toLowerCase().includes(minorSearch.toLowerCase()))
                      ).length === 0 && (
                        <div className="px-4 py-3 text-sm text-slate-400 text-center">No minors found</div>
                      )}
                    </div>
                  )}
                  {showMinorDropdown && (
                    <div className="fixed inset-0 z-40" onClick={() => setShowMinorDropdown(false)} />
                  )}
                </div>

                {/* Concentration Selection - Only show if major has concentrations */}
                {concentrationsList.length > 0 && (
                  <div className="relative">
                    <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Concentration <span className="font-normal normal-case">({concentrationsList.length})</span></label>
                    <input
                      type="text"
                      value={concentrationSearch || (authForm.concentration ? (concentrationsList.find(c => c.code === authForm.concentration)?.name || '') : '')}
                      onChange={(e) => {
                        setConcentrationSearch(e.target.value)
                        setShowConcentrationDropdown(true)
                      }}
                      onFocus={() => setShowConcentrationDropdown(true)}
                      placeholder="Search concentrations..."
                      className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                    />
                    {showConcentrationDropdown && (
                      <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                        <button
                          type="button"
                          onClick={() => {
                            setAuthForm({ ...authForm, concentration: '' })
                            setConcentrationSearch('')
                            setShowConcentrationDropdown(false)
                          }}
                          className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${!authForm.concentration ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                        >
                          <div className="font-medium">General (No Concentration)</div>
                        </button>
                        {concentrationsList
                          .filter(c =>
                            !concentrationSearch ||
                            c.name.toLowerCase().includes(concentrationSearch.toLowerCase()) ||
                            c.code.toLowerCase().includes(concentrationSearch.toLowerCase())
                          )
                          .map(c => (
                            <button
                              key={c.code}
                              type="button"
                              onClick={() => {
                                setAuthForm({ ...authForm, concentration: c.code })
                                setConcentrationSearch('')
                                setShowConcentrationDropdown(false)
                              }}
                              className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${authForm.concentration === c.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                            >
                              <div className="font-medium">{c.name}</div>
                              <div className={`text-xs ${authForm.concentration === c.code ? 'text-slate-300' : 'text-slate-400'}`}>{c.code}</div>
                            </button>
                          ))
                        }
                      </div>
                    )}
                    {showConcentrationDropdown && (
                      <div className="fixed inset-0 z-40" onClick={() => setShowConcentrationDropdown(false)} />
                    )}
                  </div>
                )}

                {/* Year Selection */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Start Year</label>
                    <select value={authForm.startYear} onChange={(e) => setAuthForm({ ...authForm, startYear: parseInt(e.target.value) })}
                      className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base appearance-none">
                      {[...Array(10)].map((_, i) => {
                        const year = new Date().getFullYear() - 5 + i
                        return <option key={year} value={year}>{year}</option>
                      })}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Graduation</label>
                    <select value={authForm.gradYear} onChange={(e) => setAuthForm({ ...authForm, gradYear: parseInt(e.target.value) })}
                      className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base appearance-none">
                      {[...Array(10)].map((_, i) => {
                        const year = new Date().getFullYear() + i
                        return <option key={year} value={year}>{year}</option>
                      })}
                    </select>
                  </div>
                </div>

                {authError && <p className="text-red-600 text-xs">{authError}</p>}
                <button type="submit" className="w-full py-3 bg-slate-900 text-white font-serif text-base hover:bg-slate-800 transition-colors mt-2" disabled={authLoading}>
                  {authLoading ? 'Please wait...' : 'Create Account'}
                </button>
                <p className="text-center text-slate-500 text-xs mt-4 pt-4 border-t border-slate-200">
                  Already have an account? <button type="button" onClick={() => setAuthMode('login')} className="text-slate-900 font-medium underline underline-offset-4">Log in</button>
                </p>
              </form>
            )}
          </div>
        </div>
      </div>
    )
  }

  // =====================
  // MAIN APP
  // =====================
  return (
    <div className="min-h-screen bg-[#FDFCF8]">
      {/* Nav - Editorial Style */}
      <nav className="bg-white border-b border-slate-900 px-6 py-3 sticky top-0 z-50">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-900 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <span className="font-serif font-medium text-slate-900 text-lg">VT Optimizer</span>
          </div>

          <div className="flex gap-1">
            {['home', 'upload', 'planner'].map(view => (
              <button key={view} onClick={() => setCurrentView(view)}
                className={`px-4 py-2 text-sm font-medium transition-colors ${currentView === view ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'}`}>
                {view === 'planner' ? 'Planner' : view.charAt(0).toUpperCase() + view.slice(1)}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setCurrentView('profile')}
              className={`flex items-center gap-2 px-3 py-2 text-sm font-medium transition-colors ${currentView === 'profile' ? 'bg-slate-900 text-white' : 'text-slate-700 hover:text-slate-900'}`}>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              {user.name}
            </button>
            <button onClick={handleLogout} className="px-3 py-2 text-sm text-slate-500 hover:text-slate-900 underline underline-offset-4 transition-colors">Logout</button>
          </div>
        </div>
      </nav>

      {/* Email Verification Banner */}
      {user && !user.email_verified && (
        <div className="bg-amber-50 border-b border-amber-600 px-6 py-3">
          <div className="flex items-center justify-center gap-4 max-w-7xl mx-auto">
            <span className="text-amber-800 text-sm">
              Please verify your email address to access all features.
            </span>
            <button
              onClick={handleResendVerification}
              disabled={authLoading}
              className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium transition-colors">
              {authLoading ? 'Sending...' : 'Resend Email'}
            </button>
          </div>
        </div>
      )}

      {/* HOME */}
      {currentView === 'home' && (
        <div className="max-w-3xl mx-auto p-8">
          <div className="text-center mb-8">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Welcome back</p>
            <h2 className="text-3xl font-serif font-medium text-slate-900 mb-3">{user.name}</h2>
            <div className="w-16 h-px bg-slate-900 mx-auto mb-4"></div>
            <p className="text-slate-600">
              {majorsList.find(m => m.code === user.major)?.name || user.major}
              {user.minor && <span className="text-slate-400"> · {minorsList.find(m => m.code === user.minor)?.name || user.minor}</span>}
            </p>
            <p className="text-slate-400 text-sm mt-1">
              Class of {user.grad_year || user.gradYear || 2028}
            </p>
          </div>

          {/* Quick Actions - Editorial Cards */}
          <div className="grid grid-cols-2 gap-6 mb-10">
            <button onClick={() => setCurrentView('upload')} className="bg-white p-6 border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] text-left hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Action</p>
              <h3 className="font-serif text-xl mb-2">Upload DARS</h3>
              <p className="text-sm text-slate-500">Import your degree audit</p>
            </button>
            <button onClick={() => setCurrentView('planner')} className="bg-white p-6 border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] text-left hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Action</p>
              <h3 className="font-serif text-xl mb-2">Course Planner</h3>
              <p className="text-sm text-slate-500">Plan your semesters</p>
            </button>
          </div>

          {/* Degree Progress Tracker - Editorial Style */}
          <div className="bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-slate-900 flex items-center justify-center text-white font-serif text-lg">%</div>
              <h3 className="text-xl font-serif">Degree Progress</h3>
            </div>

            {/* Overall Progress Circle */}
            <div className="flex items-center gap-8 mb-6 pb-6 border-b border-slate-300">
              <div className="relative w-28 h-28">
                <svg className="w-28 h-28 transform -rotate-90">
                  <circle cx="56" cy="56" r="48" stroke="#e2e8f0" strokeWidth="8" fill="none" />
                  <circle
                    cx="56" cy="56" r="48"
                    stroke="#0f172a"
                    strokeWidth="8"
                    fill="none"
                    strokeLinecap="square"
                    strokeDasharray={`${degreeProgress.overall.percentWithPlanned * 3.01} 999`}
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-3xl font-serif text-slate-900">{degreeProgress.overall.percentWithPlanned}%</span>
                  <span className="text-xs uppercase tracking-widest text-slate-500">Complete</span>
                </div>
              </div>
              <div className="flex-1">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="border border-green-600 bg-green-50 p-4">
                    <div className="text-green-700 font-serif text-xl">{degreeProgress.overall.completedCredits}</div>
                    <div className="text-green-600 text-xs uppercase tracking-widest">Credits Earned</div>
                  </div>
                  <div className="border border-blue-600 bg-blue-50 p-4">
                    <div className="text-blue-700 font-serif text-xl">{degreeProgress.overall.plannedCredits}</div>
                    <div className="text-blue-600 text-xs uppercase tracking-widest">Credits Planned</div>
                  </div>
                  <div className="border border-amber-600 bg-amber-50 p-4">
                    <div className="text-amber-700 font-serif text-xl">{degreeProgress.overall.remainingCredits}</div>
                    <div className="text-amber-600 text-xs uppercase tracking-widest">Credits Remaining</div>
                  </div>
                  <div className="border border-slate-300 bg-slate-50 p-4">
                    <div className="text-slate-700 font-serif text-xl">120</div>
                    <div className="text-slate-600 text-xs">Total Required</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Progress Bars */}
            <div className="space-y-4">
              {Object.entries(degreeProgress.categories).map(([key, cat]) => {
                const colorMap = {
                  blue: { bg: 'bg-blue-100', bar: 'bg-blue-500', text: 'text-blue-700' },
                  indigo: { bg: 'bg-indigo-100', bar: 'bg-indigo-500', text: 'text-indigo-700' },
                  green: { bg: 'bg-green-100', bar: 'bg-green-500', text: 'text-green-700' },
                  teal: { bg: 'bg-teal-100', bar: 'bg-teal-500', text: 'text-teal-700' },
                  emerald: { bg: 'bg-emerald-100', bar: 'bg-emerald-500', text: 'text-emerald-700' },
                  purple: { bg: 'bg-purple-100', bar: 'bg-purple-500', text: 'text-purple-700' },
                  pink: { bg: 'bg-pink-100', bar: 'bg-pink-500', text: 'text-pink-700' }
                }
                const colors = colorMap[cat.color] || colorMap.blue
                return (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-slate-700">{cat.name}</span>
                      <span className={`text-xs font-medium ${colors.text}`}>
                        {cat.completed?.length || 0}/{cat.required?.length || cat.minCourses || 1}
                        {cat.planned?.length > 0 && <span className="text-slate-400 ml-1">(+{cat.planned.length} planned)</span>}
                      </span>
                    </div>
                    <div className={`h-2 rounded-full ${colors.bg}`}>
                      <div
                        className={`h-2 rounded-full ${colors.bar} transition-all duration-500`}
                        style={{ width: `${cat.percent}%` }}
                      />
                    </div>
                    {cat.remaining && cat.remaining.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {cat.remaining.slice(0, 3).map(c => (
                          <span key={c} className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded">{c}</span>
                        ))}
                        {cat.remaining.length > 3 && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded">+{cat.remaining.length - 3} more</span>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* PROFILE */}
      {currentView === 'profile' && (
        <div className="max-w-lg mx-auto p-8">
          <div className="bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
            {/* Profile Header - Editorial Style */}
            <div className="bg-slate-900 px-8 py-10 text-white">
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 bg-white text-slate-900 flex items-center justify-center text-2xl font-serif font-medium">
                  {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div>
                  <h2 className="text-2xl font-serif">{user?.name}</h2>
                  <p className="text-slate-400 text-sm mt-1">{user?.email}</p>
                </div>
              </div>
            </div>

            {/* Profile Form - Editorial Style */}
            <form onSubmit={handleProfileUpdate} className="p-8 space-y-5">
              {profileMessage && (
                <div className={`p-3 text-sm ${profileMessage.type === 'success' ? 'bg-green-50 text-green-700 border border-green-600' : 'bg-red-50 text-red-700 border border-red-600'}`}>
                  {profileMessage.text}
                </div>
              )}

              {/* Name */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Name</label>
                <input
                  type="text"
                  value={profileForm.name}
                  onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
                  className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                  required
                />
              </div>

              {/* Major - Searchable */}
              <div className="relative">
                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Major <span className="font-normal normal-case">({majorsList.length})</span></label>
                <input
                  type="text"
                  value={profileMajorSearch || (majorsList.find(m => m.code === profileForm.major)?.name || '')}
                  onChange={(e) => {
                    setProfileMajorSearch(e.target.value)
                    setShowProfileMajorDropdown(true)
                  }}
                  onFocus={() => setShowProfileMajorDropdown(true)}
                  placeholder="Search majors..."
                  className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                />
                {showProfileMajorDropdown && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                    {majorsList
                      .filter(m =>
                        !profileMajorSearch ||
                        m.name.toLowerCase().includes(profileMajorSearch.toLowerCase()) ||
                        m.code.toLowerCase().includes(profileMajorSearch.toLowerCase()) ||
                        m.college.toLowerCase().includes(profileMajorSearch.toLowerCase())
                      )
                      .map(m => (
                        <button
                          key={m.code}
                          type="button"
                          onClick={() => {
                            setProfileForm({ ...profileForm, major: m.code, concentration: '' })
                            setProfileMajorSearch('')
                            setShowProfileMajorDropdown(false)
                          }}
                          className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${profileForm.major === m.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                        >
                          <div className="font-medium">{m.name}</div>
                          <div className={`text-xs ${profileForm.major === m.code ? 'text-slate-300' : 'text-slate-400'}`}>{m.college} • {m.code}</div>
                        </button>
                      ))
                    }
                    {majorsList.filter(m =>
                      !profileMajorSearch ||
                      m.name.toLowerCase().includes(profileMajorSearch.toLowerCase()) ||
                      m.code.toLowerCase().includes(profileMajorSearch.toLowerCase())
                    ).length === 0 && (
                      <div className="px-4 py-3 text-sm text-slate-400 text-center">No majors found</div>
                    )}
                  </div>
                )}
                {showProfileMajorDropdown && (
                  <div className="fixed inset-0 z-40" onClick={() => setShowProfileMajorDropdown(false)} />
                )}
              </div>

              {/* Minor - Searchable (Optional) */}
              <div className="relative">
                <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Minor <span className="font-normal normal-case">(Optional)</span></label>
                <input
                  type="text"
                  value={profileMinorSearch || (profileForm.minor ? (minorsList.find(m => m.code === profileForm.minor)?.name || '') : '')}
                  onChange={(e) => {
                    setProfileMinorSearch(e.target.value)
                    setShowProfileMinorDropdown(true)
                  }}
                  onFocus={() => setShowProfileMinorDropdown(true)}
                  placeholder="Search minors..."
                  className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                />
                {showProfileMinorDropdown && (
                  <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileForm({ ...profileForm, minor: '' })
                        setProfileMinorSearch('')
                        setShowProfileMinorDropdown(false)
                      }}
                      className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${!profileForm.minor ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                    >
                      <div className="font-medium">No Minor</div>
                    </button>
                    {minorsList
                      .filter(m => m.code !== 'NONE')
                      .filter(m =>
                        !profileMinorSearch ||
                        m.name.toLowerCase().includes(profileMinorSearch.toLowerCase()) ||
                        m.code.toLowerCase().includes(profileMinorSearch.toLowerCase())
                      )
                      .map(m => (
                        <button
                          key={m.code}
                          type="button"
                          onClick={() => {
                            setProfileForm({ ...profileForm, minor: m.code })
                            setProfileMinorSearch('')
                            setShowProfileMinorDropdown(false)
                          }}
                          className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${profileForm.minor === m.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                        >
                          <div className="font-medium">{m.name}</div>
                          <div className={`text-xs ${profileForm.minor === m.code ? 'text-slate-300' : 'text-slate-400'}`}>{m.code}</div>
                        </button>
                      ))
                    }
                    {minorsList.filter(m =>
                      m.code !== 'NONE' && (!profileMinorSearch ||
                      m.name.toLowerCase().includes(profileMinorSearch.toLowerCase()) ||
                      m.code.toLowerCase().includes(profileMinorSearch.toLowerCase()))
                    ).length === 0 && (
                      <div className="px-4 py-3 text-sm text-slate-400 text-center">No minors found</div>
                    )}
                  </div>
                )}
                {showProfileMinorDropdown && (
                  <div className="fixed inset-0 z-40" onClick={() => setShowProfileMinorDropdown(false)} />
                )}
              </div>

              {/* Concentration - Only show if major has concentrations */}
              {profileConcentrationsList.length > 0 && (
                <div className="relative">
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Concentration <span className="font-normal normal-case">({profileConcentrationsList.length})</span></label>
                  <input
                    type="text"
                    value={profileConcentrationSearch || (profileForm.concentration ? (profileConcentrationsList.find(c => c.code === profileForm.concentration)?.name || '') : '')}
                    onChange={(e) => {
                      setProfileConcentrationSearch(e.target.value)
                      setShowProfileConcentrationDropdown(true)
                    }}
                    onFocus={() => setShowProfileConcentrationDropdown(true)}
                    placeholder="Search concentrations..."
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base"
                  />
                  {showProfileConcentrationDropdown && (
                    <div className="absolute z-50 w-full mt-1 bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] max-h-48 overflow-y-auto">
                      <button
                        type="button"
                        onClick={() => {
                          setProfileForm({ ...profileForm, concentration: '' })
                          setProfileConcentrationSearch('')
                          setShowProfileConcentrationDropdown(false)
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${!profileForm.concentration ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                      >
                        <div className="font-medium">General (No Concentration)</div>
                      </button>
                      {profileConcentrationsList
                        .filter(c =>
                          !profileConcentrationSearch ||
                          c.name.toLowerCase().includes(profileConcentrationSearch.toLowerCase()) ||
                          c.code.toLowerCase().includes(profileConcentrationSearch.toLowerCase())
                        )
                        .map(c => (
                          <button
                            key={c.code}
                            type="button"
                            onClick={() => {
                              setProfileForm({ ...profileForm, concentration: c.code })
                              setProfileConcentrationSearch('')
                              setShowProfileConcentrationDropdown(false)
                            }}
                            className={`w-full text-left px-4 py-2.5 text-sm border-b border-slate-200 hover:bg-slate-50 ${profileForm.concentration === c.code ? 'bg-slate-900 text-white hover:bg-slate-800' : ''}`}
                          >
                            <div className="font-medium">{c.name}</div>
                            <div className={`text-xs ${profileForm.concentration === c.code ? 'text-slate-300' : 'text-slate-400'}`}>{c.code}</div>
                          </button>
                        ))
                      }
                    </div>
                  )}
                  {showProfileConcentrationDropdown && (
                    <div className="fixed inset-0 z-40" onClick={() => setShowProfileConcentrationDropdown(false)} />
                  )}
                </div>
              )}

              {/* Year Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Start Year</label>
                  <select
                    value={profileForm.startYear}
                    onChange={(e) => setProfileForm({ ...profileForm, startYear: parseInt(e.target.value) })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base appearance-none"
                  >
                    {[...Array(10)].map((_, i) => {
                      const year = new Date().getFullYear() - 5 + i
                      return <option key={year} value={year}>{year}</option>
                    })}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">Graduation</label>
                  <select
                    value={profileForm.gradYear}
                    onChange={(e) => setProfileForm({ ...profileForm, gradYear: parseInt(e.target.value) })}
                    className="w-full bg-transparent border-b border-slate-300 py-2 focus:border-slate-900 focus:outline-none transition-colors text-base appearance-none"
                  >
                    {[...Array(10)].map((_, i) => {
                      const year = new Date().getFullYear() + i
                      return <option key={year} value={year}>{year}</option>
                    })}
                  </select>
                </div>
              </div>

              {/* Current Info Display */}
              <div className="border border-slate-300 p-4 mt-4">
                <h4 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Current Settings</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-slate-500">Major:</div>
                  <div className="font-medium">{majorsList.find(m => m.code === user?.major)?.name || user?.major}</div>
                  {user?.minor && (
                    <>
                      <div className="text-slate-500">Minor:</div>
                      <div className="font-medium">{minorsList.find(m => m.code === user?.minor)?.name || user?.minor}</div>
                    </>
                  )}
                  {user?.concentration && (
                    <>
                      <div className="text-slate-500">Concentration:</div>
                      <div className="font-medium">{profileConcentrationsList.find(c => c.code === user?.concentration)?.name || user?.concentration}</div>
                    </>
                  )}
                  <div className="text-slate-500">Class of:</div>
                  <div className="font-medium">{user?.grad_year || user?.gradYear}</div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={profileLoading}
                className="w-full py-3 bg-slate-900 text-white font-serif hover:bg-slate-800 transition-colors disabled:opacity-50 mt-2"
              >
                {profileLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* UPLOAD */}
      {currentView === 'upload' && (
        <div className="max-w-md mx-auto p-8">
          <div className="bg-white border border-slate-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-8">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500 text-center mb-2">Import</p>
            <h2 className="text-2xl font-serif text-center mb-6">Upload DARS</h2>
            <div className="w-16 h-px bg-slate-900 mx-auto mb-6"></div>
            <label className="block cursor-pointer text-center p-10 border-2 border-dashed border-slate-300 hover:border-slate-900 transition-colors">
              <div className="w-12 h-12 mx-auto mb-4 border border-slate-900 flex items-center justify-center">
                <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span className="text-sm font-medium text-slate-700">{file ? file.name : 'Drop your DARS file here'}</span>
              <p className="text-xs text-slate-400 mt-2">PDF or TXT accepted</p>
              <input type="file" className="hidden" accept=".pdf,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            </label>
            {error && <p className="text-red-600 text-xs mt-4 text-center border border-red-600 bg-red-50 p-2">{error}</p>}
            {file && (
              <button className="w-full mt-6 py-3 bg-slate-900 text-white font-serif hover:bg-slate-800 transition-colors" onClick={handleUpload} disabled={loading}>
                {loading ? 'Analyzing...' : 'Analyze DARS'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* PLANNER */}
      {currentView === 'planner' && (
        <div className="flex flex-col md:flex-row h-[calc(100vh-52px)]">
          {/* Left Sidebar - Hidden on mobile, shown on md+ */}
          <div className="hidden md:flex w-72 bg-white border-r border-slate-900 overflow-hidden flex-col">
            <div className="p-4 border-b border-slate-300">
              <h3 className="font-serif text-lg mb-3">Course Library</h3>

              {/* Tabs - Editorial style */}
              <div className="flex flex-wrap gap-1 mb-3">
                {['required', 'electives', 'pathways', 'all'].map(tab => (
                  <button key={tab} onClick={() => setSidebarTab(tab)}
                    className={`px-3 py-1.5 text-xs font-medium transition-colors ${sidebarTab === tab ? 'bg-slate-900 text-white' : 'border border-slate-300 hover:border-slate-900 text-slate-600'}`}>
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>

              {/* Search */}
              <input
                type="text"
                value={courseSearch}
                onChange={(e) => setCourseSearch(e.target.value)}
                placeholder="Search courses..."
                className="w-full bg-transparent border-b border-slate-300 py-2 text-sm focus:border-slate-900 focus:outline-none transition-colors"
              />

              {/* Filters */}
              {sidebarTab === 'all' && (
                <div className="flex gap-1 mt-3">
                  <select
                    value={courseFilter.difficulty}
                    onChange={(e) => setCourseFilter({ ...courseFilter, difficulty: e.target.value })}
                    className="flex-1 text-xs bg-transparent border-b border-slate-300 py-1 focus:border-slate-900 focus:outline-none">
                    <option value="">All Difficulty</option>
                    <option value="1">★ Easy</option>
                    <option value="2">★★</option>
                    <option value="3">★★★</option>
                    <option value="4">★★★★</option>
                    <option value="5">★★★★★ Hard</option>
                  </select>
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-4">
              {sidebarTab === 'required' && ['cs_core', 'math_core', 'math_discrete', 'stats', 'science'].map(cat => (
                <div key={cat}>
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">{CATEGORY_INFO[cat]?.name}</h4>
                  {(coursesByCategory[cat] || []).map(code => {
                    const info = allCourses[code]
                    const isCompleted = completedCodes.has(code)
                    const isPlanned = allPlannedCourses.has(code)
                    const bestProf = info.professors?.sort((a, b) => b.rating - a.rating)[0]

                    return (
                      <div key={code}
                        draggable={true}
                        onDragStart={(e) => handleDragStart(e, code, 'library')}
                        onDragEnd={handleDragEnd}
                        onClick={() => setSelectedCourse(code)}
                        className={`group px-3 py-2.5 text-[11px] mb-2 transition-all select-none cursor-grab active:cursor-grabbing
                          ${isCompleted ? 'bg-green-50 text-green-700 border border-green-600' :
                            isPlanned ? 'bg-blue-50 text-blue-700 border border-blue-600' :
                            'bg-white border border-slate-300 hover:border-slate-900 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'}
                          ${draggedCourse === code ? 'opacity-50 border-slate-900 scale-95' : ''}
                        `}
                        style={{ touchAction: 'none' }}>
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-800">{code}</span>
                          <span className="text-[9px] text-slate-400">{'★'.repeat(info.difficulty || 3)}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 leading-tight mt-0.5">{info.name}</div>
                        {bestProf && <div className="text-[9px] text-slate-500 mt-0.5">{bestProf.name} ({bestProf.rating}★)</div>}
                        {isCompleted && <div className="text-[9px] text-green-700 font-medium mt-1">✓ Completed</div>}
                        {isPlanned && !isCompleted && <div className="text-[9px] text-blue-700 font-medium mt-1">Planned</div>}
                      </div>
                    )
                  })}
                </div>
              ))}

              {sidebarTab === 'electives' && ['cs_elective', 'cs_theory', 'cs_systems', 'capstone'].map(cat => (
                <div key={cat} className="mb-4">
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">{CATEGORY_INFO[cat]?.name}</h4>
                  {(coursesByCategory[cat] || []).map(code => {
                    const info = allCourses[code]
                    const isCompleted = completedCodes.has(code)
                    const isPlanned = allPlannedCourses.has(code)
                    const bestProf = info?.professors?.sort((a, b) => b.rating - a.rating)[0]
                    return (
                      <div key={code}
                        draggable={true}
                        onDragStart={(e) => handleDragStart(e, code, 'library')}
                        onDragEnd={handleDragEnd}
                        onClick={() => setSelectedCourse(code)}
                        className={`group px-3 py-2.5 text-[11px] mb-2 transition-all select-none cursor-grab active:cursor-grabbing
                          ${isCompleted ? 'bg-green-50 text-green-700 border border-green-600' :
                            isPlanned ? 'bg-blue-50 text-blue-700 border border-blue-600' :
                            'bg-white border border-slate-300 hover:border-slate-900 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'}
                          ${draggedCourse === code ? 'opacity-50 border-slate-900 scale-95' : ''}
                        `}
                        style={{ touchAction: 'none' }}>
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-800">{code}</span>
                          <span className="text-[9px] text-slate-400">{'★'.repeat(info?.difficulty || 3)}</span>
                        </div>
                        <div className="text-[10px] text-slate-500 leading-tight mt-0.5">{info?.name}</div>
                        {bestProf && <div className="text-[9px] text-slate-500 mt-0.5">{bestProf.name} ({bestProf.rating}★)</div>}
                        <div className="flex flex-wrap gap-1 mt-1">
                          {info?.tags?.includes('easy-elective') && <span className="text-[8px] border border-green-600 text-green-700 px-1.5 py-0.5">Easy</span>}
                          {info?.tags?.includes('hot') && <span className="text-[8px] border border-slate-900 text-slate-700 px-1.5 py-0.5">Popular</span>}
                          {isCompleted && <span className="text-[8px] bg-green-600 text-white px-1.5 py-0.5">✓ Done</span>}
                          {isPlanned && !isCompleted && <span className="text-[8px] bg-blue-600 text-white px-1.5 py-0.5">Planned</span>}
                        </div>
                      </div>
                    )
                  })}
                </div>
              ))}

              {sidebarTab === 'pathways' && (
                <div>
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">Pathways & Gen Ed</h4>
                  {(coursesByCategory['pathways'] || []).map(code => {
                    const info = allCourses[code]
                    const isCompleted = completedCodes.has(code)
                    const isPlanned = allPlannedCourses.has(code)
                    return (
                      <div key={code}
                        draggable={true}
                        onDragStart={(e) => handleDragStart(e, code, 'library')}
                        onDragEnd={handleDragEnd}
                        onClick={() => setSelectedCourse(code)}
                        className={`group px-3 py-2.5 text-[11px] mb-2 transition-all select-none cursor-grab active:cursor-grabbing
                          ${isCompleted ? 'bg-green-50 text-green-700 border border-green-600' :
                            isPlanned ? 'bg-blue-50 text-blue-700 border border-blue-600' :
                            'bg-white border border-slate-300 hover:border-slate-900 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'}
                          ${draggedCourse === code ? 'opacity-50 border-slate-900 scale-95' : ''}
                        `}
                        style={{ touchAction: 'none' }}>
                        <div className="font-semibold text-slate-800">{code}</div>
                        <div className="text-[10px] text-slate-500 leading-tight mt-0.5">{info?.name}</div>
                        {isCompleted && <div className="text-[9px] text-green-700 font-medium mt-1">✓ Completed</div>}
                        {isPlanned && !isCompleted && <div className="text-[9px] text-blue-700 font-medium mt-1">Planned</div>}
                      </div>
                    )
                  })}
                </div>
              )}

              {/* All courses with search/filter */}
              {sidebarTab === 'all' && (
                <div>
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mb-2">
                    All Courses ({Object.keys(filteredCourses).length})
                  </h4>
                  {Object.keys(filteredCourses).length === 0 ? (
                    <p className="text-xs text-slate-400 py-4 text-center">No courses match your search</p>
                  ) : (
                    Object.entries(filteredCourses).map(([code, info]) => {
                      const isCompleted = completedCodes.has(code)
                      const isPlanned = allPlannedCourses.has(code)
                      return (
                        <div key={code}
                          draggable={true}
                          onDragStart={(e) => handleDragStart(e, code, 'library')}
                          onDragEnd={handleDragEnd}
                          onClick={() => setSelectedCourse(code)}
                          className={`group px-3 py-2.5 text-[11px] mb-2 transition-all select-none cursor-grab active:cursor-grabbing
                            ${isCompleted ? 'bg-green-50 text-green-700 border border-green-600' :
                              isPlanned ? 'bg-blue-50 text-blue-700 border border-blue-600' :
                              'bg-white border border-slate-300 hover:border-slate-900 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'}
                            ${draggedCourse === code ? 'opacity-50 border-slate-900 scale-95' : ''}
                          `}
                          style={{ touchAction: 'none' }}>
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-slate-800">{code}</span>
                            <span className="text-[9px] text-slate-400">{'★'.repeat(info.difficulty || 3)}</span>
                          </div>
                          <div className="text-[10px] text-slate-500 leading-tight mt-0.5">{info.name}</div>
                          {isCompleted && <div className="text-[9px] text-green-700 font-medium mt-1">✓ Completed</div>}
                          {isPlanned && !isCompleted && <div className="text-[9px] text-blue-700 font-medium mt-1">Planned</div>}
                        </div>
                      )
                    })
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Center - Semester Grid */}
          <div className="flex-1 overflow-auto p-6 bg-[#FDFCF8]">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-serif">Graduation Plan</h2>
                {currentPlanName && <p className="text-xs text-slate-500 mt-1">Current: {currentPlanName}</p>}
              </div>
              <div className="flex gap-2 flex-wrap">
                {/* Save/Load buttons */}
                <button onClick={() => { setSavePlanName(currentPlanName || ''); setShowSaveModal(true) }}
                  className="px-3 py-1.5 bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors">
                  Save
                </button>
                <button onClick={() => setShowLoadModal(true)}
                  className="px-3 py-1.5 border border-slate-900 text-slate-900 text-xs font-medium hover:bg-slate-50 transition-colors">
                  Load
                </button>

                {/* Export buttons */}
                <button onClick={exportToPDF} disabled={exporting}
                  className="px-3 py-1.5 border border-slate-300 text-slate-600 text-xs font-medium hover:border-slate-900 transition-colors">
                  {exporting ? '...' : 'PDF'}
                </button>
                <button onClick={exportToImage} disabled={exporting}
                  className="px-3 py-1.5 border border-slate-300 text-slate-600 text-xs font-medium hover:border-slate-900 transition-colors">
                  {exporting ? '...' : 'Image'}
                </button>
                <button onClick={handleSharePlan}
                  className="px-3 py-1.5 border border-slate-300 text-slate-600 text-xs font-medium hover:border-slate-900 transition-colors">
                  Share
                </button>

                <div className="w-px bg-slate-300 mx-1"></div>

                <button onClick={() => setSemesterPlan(EMPTY_PLAN)}
                  className="px-3 py-1.5 border border-red-400 text-red-600 text-xs font-medium hover:bg-red-50 transition-colors">
                  Clear
                </button>
                <button onClick={generateOptimalSchedule}
                  className="px-3 py-1.5 bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors">
                  Auto-Generate
                </button>
                <button onClick={runAiAnalysis} disabled={analyzing}
                  className="px-3 py-1.5 bg-slate-900 text-white text-xs font-medium hover:bg-slate-800 transition-colors">
                  {analyzing ? '...' : 'Analyze'}
                </button>
              </div>
            </div>

            {/* Planning Priority & Preferences */}
            <div className="bg-white border border-slate-300 p-4 mb-6">
              <div className="flex flex-wrap items-center gap-4 mb-3">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500">Planning Mode:</span>
                <select value={planPriority} onChange={e => setPlanPriority(e.target.value)}
                  className="px-2 py-1 text-xs border border-slate-300 bg-white text-slate-900 focus:ring-slate-900 focus:border-slate-900">
                  <option value="on_time">Graduate On Time</option>
                  <option value="maximize_gpa">Maximize GPA</option>
                  <option value="career_optimized">Career Optimized</option>
                </select>
                {planPriority === 'career_optimized' && (
                  <select value={planCareerPath} onChange={e => setPlanCareerPath(e.target.value)}
                    className="px-2 py-1 text-xs border border-slate-300 bg-white text-slate-900 focus:ring-slate-900 focus:border-slate-900">
                    <option value="">Select Career Path</option>
                    <option value="software_engineering">Software Engineering</option>
                    <option value="ai_ml">AI & Machine Learning</option>
                    <option value="systems">Systems & Infrastructure</option>
                    <option value="security">Cybersecurity</option>
                    <option value="hci">Human-Computer Interaction</option>
                    <option value="data_science">Data Science</option>
                  </select>
                )}
              </div>
              <div className="flex flex-wrap gap-4">
                <span className="text-xs font-bold uppercase tracking-widest text-slate-500">Optimize for:</span>
                {[
                  { key: 'easiest', label: 'Easiest Classes' },
                  { key: 'bestProfessors', label: 'Best Professors' },
                  { key: 'leastWorkload', label: 'Least Workload' },
                  { key: 'lateTimes', label: 'Late Start Times' },
                  { key: 'balanced', label: 'Balanced Load' },
                ].map(({ key, label }) => (
                  <label key={key} className="flex items-center gap-1.5 text-xs cursor-pointer">
                    <input type="checkbox" checked={preferences[key]}
                      onChange={(e) => setPreferences(p => ({ ...p, [key]: e.target.checked }))}
                      className="w-3.5 h-3.5 border-slate-900 text-slate-900 focus:ring-slate-900" />
                    {label}
                  </label>
                ))}
              </div>
              {autoplanWarnings.length > 0 && (
                <div className="mt-3 p-2 bg-amber-50 border border-amber-200 text-xs text-amber-800">
                  {autoplanWarnings.map((w, i) => <div key={i}>{w}</div>)}
                </div>
              )}
            </div>

            {/* Semester Grid */}
            <div id="graduation-plan" className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {SEMESTERS.map(sem => {
                const courses = semesterPlan[sem.id] || []
                const credits = getSemesterCredits(sem.id)
                const isOverloaded = credits > 18

                return (
                  <div key={sem.id}
                    onDragOver={handleDragOver}
                    onDragEnter={handleDragEnter}
                    onDrop={(e) => handleDrop(e, sem.id)}
                    className={`bg-white border p-4 min-h-[200px] transition-all
                      ${draggedCourse ? 'border-slate-900 border-dashed bg-slate-50' : 'border-slate-900'}
                      ${isOverloaded ? 'border-red-500' : ''}
                      ${!draggedCourse ? 'shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]' : ''}
                    `}>
                    <div className="flex justify-between items-center mb-3 pb-2 border-b border-slate-200">
                      <h3 className="text-xs font-serif font-medium">{sem.name}</h3>
                      <span className={`text-[10px] font-medium ${isOverloaded ? 'text-red-500' : 'text-slate-500'}`}>
                        {credits} cr
                      </span>
                    </div>

                    <div className="space-y-2">
                      {courses.map(code => {
                        const info = allCourses[code]
                        const hasPrereqs = prereqsMet(code, sem.id)

                        return (
                          <div key={code}
                            draggable
                            onDragStart={(e) => handleDragStart(e, code, sem.id)}
                            onDragEnd={handleDragEnd}
                            onClick={() => setSelectedCourse(code)}
                            className={`px-2.5 py-2 text-[11px] cursor-grab active:cursor-grabbing
                              flex justify-between items-center transition-all relative border
                              ${!hasPrereqs ? 'bg-red-50 text-red-700 border-red-500' :
                                info?.category === 'cs_core' ? 'bg-blue-50 text-blue-800 border-blue-400' :
                                info?.category === 'cs_elective' ? 'bg-indigo-50 text-indigo-800 border-indigo-400' :
                                info?.category === 'cs_theory' ? 'bg-violet-50 text-violet-800 border-violet-400' :
                                info?.category === 'cs_systems' ? 'bg-purple-50 text-purple-800 border-purple-400' :
                                info?.category === 'capstone' ? 'bg-pink-50 text-pink-800 border-pink-400' :
                                info?.category?.startsWith('math') ? 'bg-green-50 text-green-800 border-green-400' :
                                info?.category === 'stats' ? 'bg-teal-50 text-teal-800 border-teal-400' :
                                info?.category === 'science' ? 'bg-amber-50 text-amber-800 border-amber-400' :
                                info?.category === 'pathways' ? 'bg-orange-50 text-orange-800 border-orange-400' :
                                'bg-slate-50 text-slate-700 border-slate-300'}
                              ${draggedCourse === code ? 'opacity-50 border-slate-900' : ''}
                            `}>
                            <div className="flex-1">
                              <div className="font-medium">{code}</div>
                              {!hasPrereqs && <div className="text-[8px]">Missing prereqs</div>}
                            </div>
                            <button
                              onClick={(e) => { e.stopPropagation(); removeCourse(code, sem.id) }}
                              className="w-6 h-6 flex items-center justify-center bg-slate-900 hover:bg-slate-700 text-white text-sm font-bold ml-2 transition-all"
                              title="Remove course">
                              ×
                            </button>
                          </div>
                        )
                      })}
                    </div>

                    {courses.length === 0 && (
                      <div className="text-center text-slate-400 text-[10px] mt-12 uppercase tracking-widest">
                        Drop courses here
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Completed */}
            {completedCodes.size > 0 && (
              <div className="mt-6 bg-white border border-slate-900 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] p-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-green-700 mb-3">Completed ({completedCodes.size})</h3>
                <div className="flex flex-wrap gap-2">
                  {[...completedCodes].map(code => (
                    <span key={code} className="px-2 py-1 bg-green-50 text-green-700 border border-green-600 text-[10px]">{code}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar - AI Analysis - Hidden on mobile */}
          <div className="hidden lg:flex w-64 bg-white border-l flex-col">
            <div className="p-3 border-b">
              <h3 className="font-semibold text-sm">AI Analysis</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-3">
              {!aiAnalysis ? (
                <div className="text-center text-slate-400 text-xs py-8">
                  <div className="text-3xl mb-2">🤖</div>
                  Click "Analyze" to get<br/>recommendations
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-center p-3 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50">
                    <div className={`text-3xl font-bold ${aiAnalysis.overallScore >= 80 ? 'text-green-600' : aiAnalysis.overallScore >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                      {aiAnalysis.overallScore}%
                    </div>
                    <div className="text-xs text-slate-500">Plan Score</div>
                  </div>

                  {aiAnalysis.issues?.length > 0 && (
                    <div>
                      <h4 className="text-[10px] font-semibold text-red-600 uppercase mb-1">Issues</h4>
                      {aiAnalysis.issues.map((issue, i) => (
                        <div key={i} className="text-[11px] text-red-700 bg-red-50 p-2 rounded mb-1">⚠️ {issue}</div>
                      ))}
                    </div>
                  )}

                  {aiAnalysis.suggestions?.length > 0 && (
                    <div>
                      <h4 className="text-[10px] font-semibold text-amber-600 uppercase mb-1">Suggestions</h4>
                      {aiAnalysis.suggestions.map((sug, i) => (
                        <div key={i} className="text-[11px] text-amber-700 bg-amber-50 p-2 rounded mb-1">💡 {sug}</div>
                      ))}
                    </div>
                  )}

                  {aiAnalysis.positives?.length > 0 && (
                    <div>
                      <h4 className="text-[10px] font-semibold text-green-600 uppercase mb-1">Looking Good</h4>
                      {aiAnalysis.positives.map((pos, i) => (
                        <div key={i} className="text-[11px] text-green-700 bg-green-50 p-2 rounded mb-1">✓ {pos}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Course Modal */}
      {selectedCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedCourse(null)}>
          <div className="bg-white rounded-xl p-5 max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="font-bold text-lg">{selectedCourse}</h2>
                <p className="text-sm text-slate-500">{allCourses[selectedCourse]?.name}</p>
              </div>
              <button onClick={() => setSelectedCourse(null)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
              <div className="bg-slate-50 p-2 rounded">
                <div className="text-[10px] text-slate-500">Credits</div>
                <div className="font-semibold">{allCourses[selectedCourse]?.credits}</div>
              </div>
              <div className="bg-slate-50 p-2 rounded">
                <div className="text-[10px] text-slate-500">Difficulty</div>
                <div className="font-semibold text-amber-600">{'★'.repeat(allCourses[selectedCourse]?.difficulty || 3)}</div>
              </div>
              <div className="bg-slate-50 p-2 rounded">
                <div className="text-[10px] text-slate-500">Workload</div>
                <div className="font-semibold">{allCourses[selectedCourse]?.workload}/5</div>
              </div>
              <div className="bg-slate-50 p-2 rounded">
                <div className="text-[10px] text-slate-500">Required</div>
                <div className="font-semibold">{allCourses[selectedCourse]?.required ? 'Yes' : 'No'}</div>
              </div>
            </div>

            <div className="mb-4">
              <div className="flex justify-between items-center mb-1">
                <span className="text-[10px] text-slate-500">Prerequisites</span>
                <button
                  onClick={() => { setPrereqCourse(selectedCourse); setShowPrereqModal(true) }}
                  className="text-[10px] text-blue-500 hover:text-blue-700">
                  View Chain →
                </button>
              </div>
              <div className="text-sm">{allCourses[selectedCourse]?.prereqs?.join(', ') || 'None'}</div>
            </div>

            <div className="mb-4">
              <div className="text-[10px] text-slate-500 mb-1">Professors</div>
              {allCourses[selectedCourse]?.professors?.map((prof, i) => (
                <div key={i} className="flex justify-between items-center bg-slate-50 p-2 rounded mb-1">
                  <span className="text-sm font-medium">{prof.name}</span>
                  <div className="text-xs">
                    <span className="text-amber-600">{prof.rating}★</span>
                    <span className="text-slate-400 ml-2">GPA: {prof.avgGPA}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="mb-4">
              <div className="text-[10px] text-slate-500 mb-1">Time Slots</div>
              <div className="flex flex-wrap gap-1">
                {allCourses[selectedCourse]?.timeSlots?.map((time, i) => (
                  <span key={i} className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{time}</span>
                ))}
              </div>
            </div>

            {!completedCodes.has(selectedCourse) && !allPlannedCourses.has(selectedCourse) && (
              <div className="border-t pt-3">
                <p className="text-xs text-slate-500 mb-2">Add to semester:</p>
                <div className="grid grid-cols-4 gap-1">
                  {SEMESTERS.map(sem => (
                    <button key={sem.id}
                      onClick={() => { addCourseToSemester(selectedCourse, sem.id); setSelectedCourse(null) }}
                      className="px-2 py-1.5 bg-slate-100 hover:bg-blue-100 rounded text-[10px] font-medium">
                      {sem.name}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Save Plan Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowSaveModal(false)}>
          <div className="bg-white rounded-xl p-5 max-w-sm w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg">Save Plan</h2>
              <button onClick={() => setShowSaveModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            <input
              type="text"
              value={savePlanName}
              onChange={(e) => setSavePlanName(e.target.value)}
              placeholder="Plan name (e.g., 'Fall 2024 Plan')"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-green-300 text-sm mb-4"
              autoFocus
            />

            <div className="flex gap-2">
              {currentPlanId && (
                <button
                  onClick={() => handleSavePlan(false)}
                  disabled={plansLoading || !savePlanName.trim()}
                  className="flex-1 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 disabled:opacity-50">
                  {plansLoading ? 'Saving...' : 'Update'}
                </button>
              )}
              <button
                onClick={() => handleSavePlan(true)}
                disabled={plansLoading || !savePlanName.trim()}
                className="flex-1 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:opacity-50">
                {plansLoading ? 'Saving...' : (currentPlanId ? 'Save as New' : 'Save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Plan Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowLoadModal(false)}>
          <div className="bg-white rounded-xl p-5 max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg">Load Plan</h2>
              <button onClick={() => setShowLoadModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            {savedPlans.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <div className="text-3xl mb-2">📋</div>
                <p>No saved plans yet.</p>
                <p className="text-xs mt-1">Create your first plan and save it!</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {savedPlans.map(plan => (
                  <div key={plan.id}
                    className={`p-3 rounded-lg border ${currentPlanId === plan.id ? 'border-green-400 bg-green-50' : 'border-slate-200 hover:border-blue-300 hover:bg-blue-50'} cursor-pointer transition-all`}>
                    <div className="flex justify-between items-start">
                      <div onClick={() => handleLoadPlan(plan)} className="flex-1">
                        <div className="font-medium text-sm flex items-center gap-2">
                          {plan.name}
                          {plan.is_default && <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">Default</span>}
                          {currentPlanId === plan.id && <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded">Current</span>}
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          {Object.values(plan.plan_data || {}).flat().length} courses planned
                        </div>
                        <div className="text-[10px] text-slate-400">
                          Updated: {new Date(plan.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDeletePlan(plan.id) }}
                        className="text-red-400 hover:text-red-600 p-1">
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => setShowLoadModal(false)}
              className="w-full mt-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200">
              Close
            </button>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowShareModal(false)}>
          <div className="bg-white rounded-xl p-5 max-w-md w-full shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg">Share Plan</h2>
              <button onClick={() => setShowShareModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            <p className="text-sm text-slate-600 mb-4">
              Share this link with your advisor or anyone you want to show your graduation plan to:
            </p>

            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm bg-slate-50"
              />
              <button
                onClick={copyShareLink}
                className={`px-4 py-2 rounded-lg font-medium text-sm ${shareCopied ? 'bg-green-500 text-white' : 'bg-purple-500 text-white hover:bg-purple-600'}`}>
                {shareCopied ? '✓ Copied!' : 'Copy'}
              </button>
            </div>

            <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700">
              <p className="font-medium mb-1">This link:</p>
              <ul className="list-disc list-inside space-y-1 text-blue-600">
                <li>Works without login (advisors don't need an account)</li>
                <li>Shows your plan in read-only mode</li>
                <li>Expires in 30 days</li>
                <li>Tracks view count</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Prerequisite Chain Modal */}
      {showPrereqModal && prereqCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setShowPrereqModal(false)}>
          <div className="bg-white rounded-xl p-5 max-w-2xl w-full shadow-2xl max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h2 className="font-bold text-lg">Prerequisite Chain: {prereqCourse}</h2>
              <button onClick={() => setShowPrereqModal(false)} className="text-slate-400 hover:text-slate-600 text-xl">×</button>
            </div>

            <p className="text-sm text-slate-500 mb-4">{allCourses[prereqCourse]?.name}</p>

            {/* Prerequisites Tree */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">What you need before taking this course:</h3>
              {(() => {
                const chain = getPrereqChain(prereqCourse)
                const renderTree = (node, level = 0) => {
                  if (!node.prereqs || node.prereqs.length === 0) {
                    return level === 0 ? (
                      <p className="text-sm text-slate-400 italic">No prerequisites</p>
                    ) : null
                  }
                  return (
                    <div className={level > 0 ? 'ml-6 border-l-2 border-blue-200 pl-4' : ''}>
                      {node.prereqs.map((prereq, i) => (
                        <div key={i} className="mb-2">
                          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm
                            ${completedCodes.has(prereq.code) ? 'bg-green-100 text-green-700' :
                              allPlannedCourses.has(prereq.code) ? 'bg-blue-100 text-blue-700' :
                              'bg-slate-100 text-slate-700'}`}>
                            <span className="font-medium">{prereq.code}</span>
                            <span className="text-xs opacity-70">{prereq.name}</span>
                            {completedCodes.has(prereq.code) && <span className="text-xs">✓</span>}
                            {allPlannedCourses.has(prereq.code) && !completedCodes.has(prereq.code) && <span className="text-xs">📅</span>}
                          </div>
                          {renderTree(prereq, level + 1)}
                        </div>
                      ))}
                    </div>
                  )
                }
                return renderTree(chain)
              })()}
            </div>

            {/* Courses that require this */}
            <div>
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Courses unlocked by completing {prereqCourse}:</h3>
              {(() => {
                const requiring = getCoursesRequiring(prereqCourse)
                if (requiring.length === 0) {
                  return <p className="text-sm text-slate-400 italic">No courses require this as a prerequisite</p>
                }
                return (
                  <div className="flex flex-wrap gap-2">
                    {requiring.map(course => (
                      <div key={course.code}
                        onClick={() => { setPrereqCourse(course.code) }}
                        className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-lg text-sm cursor-pointer hover:bg-purple-200">
                        <span className="font-medium">{course.code}</span>
                        <span className="text-xs ml-1 opacity-70">{course.name}</span>
                      </div>
                    ))}
                  </div>
                )
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
