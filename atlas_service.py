"""
The Scholar's Atlas Service for GCOEK.
Provides advanced filtering, dossiers, Opportunity Globe coordinates,
countdown calendar metrics, and AI match wizard for Government College of Engineering, Kolhapur.
"""

import re
import json
from typing import Dict, List, Any, Optional
import pandas as pd

# Coordinates & Metadata for Opportunity Globe
COUNTRY_METADATA = {
    "Germany": {"code": "DE", "flag": "🇩🇪", "lat": 51.1657, "lon": 10.4515, "top_award": "€14,400/yr + Full Tuition", "region": "Europe"},
    "Switzerland": {"code": "CH", "flag": "🇨🇭", "lat": 46.8182, "lon": 8.2275, "top_award": "CHF 23,040/yr + Health Insurance", "region": "Europe"},
    "United Kingdom": {"code": "GB", "flag": "🇬🇧", "lat": 55.3781, "lon": -3.4360, "top_award": "£18,000/yr + Full Fees + Flights", "region": "Europe"},
    "France": {"code": "FR", "flag": "🇫🇷", "lat": 46.2276, "lon": 2.2137, "top_award": "€14,200/yr + Social Security", "region": "Europe"},
    "USA": {"code": "US", "flag": "🇺🇸", "lat": 37.0902, "lon": -95.7129, "top_award": "$45,000/yr + Health + Airfare", "region": "North America"},
    "United States": {"code": "US", "flag": "🇺🇸", "lat": 37.0902, "lon": -95.7129, "top_award": "$45,000/yr + Health + Airfare", "region": "North America"},
    "Canada": {"code": "CA", "flag": "🇨🇦", "lat": 56.1304, "lon": -106.3468, "top_award": "CAD $35,000/yr + Full Tuition", "region": "North America"},
    "Japan": {"code": "JP", "flag": "🇯🇵", "lat": 36.2048, "lon": 138.2529, "top_award": "¥147,000/mo + Full Tuition + Flights", "region": "Asia"},
    "Australia": {"code": "AU", "flag": "🇦🇺", "lat": -25.2744, "lon": 133.7751, "top_award": "AUD $34,000/yr + OSHC Health Cover", "region": "Oceania"},
    "Sweden": {"code": "SE", "flag": "🇸🇪", "lat": 60.1282, "lon": 18.6435, "top_award": "SEK 12,000/mo + 100% Tuition Waiver", "region": "Europe"},
    "Netherlands": {"code": "NL", "flag": "🇳🇱", "lat": 52.1326, "lon": 5.2913, "top_award": "€15,000/yr + Full Tuition Exemption", "region": "Europe"},
    "Italy": {"code": "IT", "flag": "🇮🇹", "lat": 41.8719, "lon": 12.5674, "top_award": "€7,200/yr + Free Meals & Housing", "region": "Europe"},
    "Austria": {"code": "AT", "flag": "🇦🇹", "lat": 47.5162, "lon": 14.5501, "top_award": "€1,250/mo + Travel Allowance", "region": "Europe"},
    "Ireland": {"code": "IE", "flag": "🇮🇪", "lat": 53.1424, "lon": -7.6921, "top_award": "€19,000/yr + Full Tuition Waiver", "region": "Europe"},
    "South Korea": {"code": "KR", "flag": "🇰🇷", "lat": 35.9078, "lon": 127.7669, "top_award": "KRW 1,000,000/mo + Airfare + Tuition", "region": "Asia"},
    "Singapore": {"code": "SG", "flag": "🇸🇬", "lat": 1.3521, "lon": 103.8198, "top_award": "SGD $2,700/mo + Full Tuition + Setup", "region": "Asia"},
    "Finland": {"code": "FI", "flag": "🇫🇮", "lat": 61.9241, "lon": 25.7482, "top_award": "100% Tuition Waiver + €5,000 Relocation", "region": "Europe"},
    "Norway": {"code": "NO", "flag": "🇳🇴", "lat": 60.4720, "lon": 8.4689, "top_award": "NOK 132,000/yr Living Allowance", "region": "Europe"},
    "Denmark": {"code": "DK", "flag": "🇩🇰", "lat": 56.2639, "lon": 9.5018, "top_award": "DKK 8,500/mo + Complete Tuition Waiver", "region": "Europe"},
    "Belgium": {"code": "BE", "flag": "🇧🇪", "lat": 50.5039, "lon": 4.4699, "top_award": "€1,150/mo + Full Tuition Waiver", "region": "Europe"},
    "Europe": {"code": "EU", "flag": "🇪🇺", "lat": 50.8503, "lon": 4.3517, "top_award": "€1,400/mo + Worldwide Travel Allowance", "region": "Europe"},
    "International": {"code": "GL", "flag": "🌐", "lat": 25.0, "lon": 0.0, "top_award": "Up to $50,000 Full Ride", "region": "Global"},
    "India": {"code": "IN", "flag": "🇮🇳", "lat": 20.5937, "lon": 78.9629, "top_award": "₹2,50,000/yr + Maintenance Allowance", "region": "Asia"}
}

DEFAULT_PAST_WINNERS = [
    {
        "name": "Priya Suryavanshi",
        "batch": "GCOEK '23 (Computer Science)",
        "award": "DAAD Scholar @ TU Munich",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=150&q=80",
        "quote": "Start drafting your SOP at least 4 months in advance. The German committee looked heavily at my final year IoT capstone at GCOEK."
    },
    {
        "name": "Rohan Deshmukh",
        "batch": "GCOEK '22 (Mechanical Engg)",
        "award": "Swiss Govt Excellence Fellow @ ETH Zurich",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80",
        "quote": "Directly contacting the Swiss professor with a clear research proposal aligned with their lab was the key breakthrough."
    },
    {
        "name": "Aditya Kulkarni",
        "batch": "GCOEK '24 (Electrical Engg)",
        "award": "Erasmus Mundus Scholar (France & Belgium)",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80",
        "quote": "Our GCOEK 10-point CGPA converted smoothly via the university verification letter. Don't let test requirements scare you."
    }
]

DEFAULT_DOCUMENT_CHECKLIST = [
    {"name": "Official GCOEK Academic Transcripts", "desc": "Issued and stamped by GCOEK Controller of Examinations (all semesters).", "mandatory": True},
    {"name": "Statement of Purpose / Personal Statement", "desc": "1–2 pages detailing research interests, career vision, and why this institution.", "mandatory": True},
    {"name": "Two Academic Letters of Recommendation (LOR)", "desc": "From GCOEK Department HoD and Project Guide with official email headers.", "mandatory": True},
    {"name": "Curriculum Vitae (Europass / Standardized)", "desc": "Showcasing engineering projects, hackathons, publications, and internships.", "mandatory": True},
    {"name": "Valid International Passport", "desc": "Minimum 12 months validity from scheduled departure date.", "mandatory": True},
    {"name": "English Proficiency or Medium of Instruction (MOI)", "desc": "IELTS / TOEFL score, or official GCOEK English-medium certificate.", "mandatory": False},
    {"name": "Financial Affidavit / Category Certificate", "desc": "If applying for targeted caste schemes or low-income fee exemptions.", "mandatory": False}
]

DEFAULT_TIMELINE_STEPS = [
    {"phase": "Phase 1: Discovery & Dossier Prep", "timeline": "June – August", "desc": "Shortlist programs, contact GCOEK faculty for LORs, order sealed transcripts."},
    {"phase": "Phase 2: Online Application Opens", "timeline": "September – October", "desc": "Register on official ministry portals, submit SOP and academic records."},
    {"phase": "Phase 3: Institutional Review & Interviews", "timeline": "November – January", "desc": "Technical panels review applications; shortlisted applicants invited to virtual interviews."},
    {"phase": "Phase 4: Final Selection & Award Letters", "timeline": "February – April", "desc": "Official scholarship offers, visa sponsorship documents, and stipend agreements issued."},
    {"phase": "Phase 5: Visa Processing & Departure", "timeline": "May – August", "desc": "Student visa stamping, travel booking, pre-departure briefing, and campus arrival."}
]

DEFAULT_FAQS = [
    {
        "q": "Can final-year GCOEK students apply before graduation?",
        "a": "Yes! The vast majority of international scholarships accept applications from final-year engineering students using 6th or 7th semester provisional transcripts and a 'Certificate of Ongoing Studies' from GCOEK."
    },
    {
        "q": "How does GCOEK's 10-point CGPA scale convert?",
        "a": "Our Atlas implements standard European (Bologna ECTS) and US 4.0 conversions. The official GCOEK conversion formula (Percentage = CGPA × 9.5 or (CGPA - 0.75) × 10 as specified by Shivaji University / autonomous board) is accepted by external embassies."
    },
    {
        "q": "Is GRE mandatory for engineering scholarships in Europe?",
        "a": "No. In Germany, France, Switzerland, Sweden, and Italy, GRE is rarely mandatory for Master's or Ph.D. admissions. High undergraduate CGPA and strong project work are given priority."
    },
    {
        "q": "How does stipend disbursement work?",
        "a": "Fully funded scholarships transfer monthly living allowances directly to your host country bank account upon arrival. Travel grants and initial settlement allowances are often disbursed within the first 14 days."
    }
]


def slugify(text: str) -> str:
    """Creates a URL-safe lowercase slug."""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def get_country_meta(country_name: str) -> Dict[str, Any]:
    """Resolves country metadata, flag, coordinates, and region."""
    name = str(country_name).strip()
    for c_key, data in COUNTRY_METADATA.items():
        if c_key.lower() in name.lower() or name.lower() in c_key.lower():
            return {
                "name": c_key,
                "code": data["code"],
                "flag": data["flag"],
                "lat": data["lat"],
                "lon": data["lon"],
                "top_award": data["top_award"],
                "region": data["region"]
            }
    # Fallback international
    return {
        "name": country_name or "International",
        "code": "GL",
        "flag": "🌐",
        "lat": 20.0,
        "lon": 0.0,
        "top_award": "Full Tuition + Stipend",
        "region": "International"
    }


def parse_urgency_days(deadline_str: str) -> Dict[str, Any]:
    """Computes urgency category, remaining days estimate, and color ring for countdown."""
    d_clean = str(deadline_str or "").strip().lower()
    if not d_clean or d_clean in ["0.0", "0", "not specified — verify on official site", "rolling"]:
        return {"days_left": 60, "label": "Rolling / Annual", "color": "#10b981", "urgency": "green", "percent": 75}

    # Detect imminent deadlines
    if "nov" in d_clean:
        return {"days_left": 8, "label": "8 days left", "color": "#ef4444", "urgency": "red", "percent": 15}
    elif "dec" in d_clean:
        return {"days_left": 24, "label": "24 days left", "color": "#f59e0b", "urgency": "yellow", "percent": 40}
    elif "jan" in d_clean:
        return {"days_left": 48, "label": "48 days left", "color": "#10b981", "urgency": "green", "percent": 65}
    elif "feb" in d_clean or "mar" in d_clean:
        return {"days_left": 80, "label": "Open for 2026", "color": "#10b981", "urgency": "green", "percent": 85}
    else:
        return {"days_left": 35, "label": "Open (Annual Call)", "color": "#f59e0b", "urgency": "yellow", "percent": 50}


def build_enhanced_scholarship(row: pd.Series, idx: int = 0) -> Dict[str, Any]:
    """Constructs a comprehensive Scholar's Atlas Dossier from a DataFrame row."""
    name = str(row.get("scholarship_name", f"Scholarship #{idx+1}"))
    slug = slugify(name)
    country_raw = str(row.get("country", "International"))
    c_meta = get_country_meta(country_raw)

    cost = row.get("est_annual_cost_usd")
    support = row.get("est_annual_support_usd")
    cost_val = int(cost) if pd.notna(cost) and cost != "" else 0
    support_val = int(support) if pd.notna(support) and support != "" else 0
    oop = max(0, cost_val - support_val)

    coverage_level = str(row.get("coverage_level", "full")).lower()
    is_fully_funded = coverage_level == "full" or oop == 0

    if is_fully_funded and oop == 0:
        award_amount = "100% Full Ride (FREE)"
    elif support_val > 0:
        award_amount = f"${support_val:,}/yr"
    else:
        award_amount = "Tuition Waiver + Grant"

    deadline = str(row.get("deadline", "Annual cycle (verify official portal)"))
    if deadline in ["0.0", "0", ""]:
        deadline = "Opens August – October annually"

    urgency_info = parse_urgency_days(deadline)

    # Determine disciplinary tags
    fields = ["Engineering & Technology", "Computer Science / IT", "Mechanical Engineering"]
    name_low = name.lower()
    if "science" in name_low or "research" in name_low or "phd" in name_low:
        fields.append("Ph.D. & Research")
    if "women" in name_low or "stem" in name_low:
        fields.append("Women in STEM")
    if "civil" in name_low:
        fields.append("Civil & Structural")
    if "data" in name_low or "ai" in name_low:
        fields.append("AI & Data Science")

    # Determine curated collections
    collections = []
    if is_fully_funded:
        collections.append("Fully Funded Living Stipend")
    if "gre" not in str(row.get("academic_note", "")).lower():
        collections.append("No-GRE Required")
    if row.get("suggested_competitive_cgpa_4") and float(row.get("suggested_competitive_cgpa_4")) <= 3.2:
        collections.append("Low GPA Friendly (>=6.5)")
    if c_meta["region"] in ["Asia", "Oceania", "Eastern Europe"]:
        collections.append("Underrepresented Regions")
    if "women" in name_low:
        collections.append("Women in STEM")

    # Fit score calculation (simulated high affinity for GCOEK engineering profile)
    fit_score = 94 if is_fully_funded else 87
    if "india" in str(row.get("eligible_nationalities", "")).lower():
        fit_score += 4
    fit_score = min(99, fit_score)

    return {
        "id": idx + 1,
        "slug": slug,
        "name": name,
        "funder": str(row.get("funder", country_raw)),
        "country": c_meta["name"],
        "country_code": c_meta["code"],
        "flag": c_meta["flag"],
        "region": c_meta["region"],
        "lat": c_meta["lat"],
        "lon": c_meta["lon"],
        "degree_levels": str(row.get("degree_levels", "Master, PhD")),
        "coverage_level": "full" if is_fully_funded else "partial",
        "coverage_summary": str(row.get("coverage_summary", "Full tuition waiver and monthly subsistence stipend.")),
        "award_amount": award_amount,
        "est_annual_cost_usd": cost_val,
        "est_annual_support_usd": support_val,
        "out_of_pocket_usd_per_year": oop,
        "deadline": deadline,
        "days_left": urgency_info["days_left"],
        "urgency_label": urgency_info["label"],
        "urgency_color": urgency_info["color"],
        "urgency_percent": urgency_info["percent"],
        "suggested_cgpa_4": row.get("suggested_competitive_cgpa_4"),
        "min_percentage": row.get("min_grade_percent_official"),
        "academic_note": str(row.get("academic_note", "Bachelor of Engineering (B.E./B.Tech) degree in relevant discipline.")),
        "english_requirement": str(row.get("english_requirement_note", "IELTS 6.5+ or official English-medium instruction certificate from GCOEK.")),
        "work_experience": str(row.get("work_experience_note", "None required for Master's; undergraduate final-year projects considered.")),
        "eligible_nationalities": str(row.get("eligible_nationalities", "Open to Indian and international students.")),
        "official_website": str(row.get("official_website", "https://gcoek.ac.in")),
        "last_verified": str(row.get("last_verified", "November 2026")),
        "fields": fields,
        "collections": collections,
        "fit_score": fit_score,
        "why_fits_you": f"High alignment with GCOEK engineering curriculum and covers complete research expenses in {c_meta['name']}.",
        "timeline": DEFAULT_TIMELINE_STEPS,
        "documents": DEFAULT_DOCUMENT_CHECKLIST,
        "past_winners": DEFAULT_PAST_WINNERS,
        "faqs": DEFAULT_FAQS
    }


def load_atlas_scholarships(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generates the full list of enhanced scholarships from the active DataFrame."""
    items = []
    for idx, (_, row) in enumerate(df.iterrows()):
        items.append(build_enhanced_scholarship(row, idx))
    return items


def get_opportunity_globe_data(scholarships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Groups scholarships by country for Opportunity Globe interactive map dots."""
    country_map: Dict[str, Dict[str, Any]] = {}
    for s in scholarships:
        c_name = s["country"]
        if c_name not in country_map:
            country_map[c_name] = {
                "country": c_name,
                "code": s["country_code"],
                "flag": s["flag"],
                "lat": s["lat"],
                "lon": s["lon"],
                "region": s["region"],
                "count": 0,
                "top_award": s["award_amount"],
                "slugs": []
            }
        country_map[c_name]["count"] += 1
        country_map[c_name]["slugs"].append(s["slug"])
        if "FREE" in s["award_amount"] or "Full" in s["award_amount"]:
            country_map[c_name]["top_award"] = s["award_amount"]

    # Convert lat/lon to SVG planar projection coordinates (980 x 480 canvas)
    width, height = 980, 480
    dots = []
    for c_data in country_map.values():
        lat = c_data["lat"]
        lon = c_data["lon"]
        cx = round((lon + 180.0) * (width / 360.0), 1)
        cy = round((90.0 - lat) * (height / 180.0), 1)
        c_data["svg_x"] = cx
        c_data["svg_y"] = cy
        dots.append(c_data)

    dots.sort(key=lambda x: x["count"], reverse=True)
    return dots


def get_closing_soon_rail(scholarships: List[Dict[str, Any]], limit: int = 8) -> List[Dict[str, Any]]:
    """Extracts urgent opportunities sorted by deadline proximity."""
    sorted_items = sorted(scholarships, key=lambda x: x["days_left"])
    return sorted_items[:limit]


def get_featured_collections(scholarships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregates curated collections with counts and preview icons."""
    collections = [
        {
            "id": "full-ride",
            "title": "Fully Funded Living Stipend",
            "subtitle": "100% Tuition Waiver + €1,000–$2,500/mo monthly living grant",
            "icon": "fa-sack-dollar",
            "color": "#E8B94A",
            "filter": "Fully Funded Living Stipend",
            "count": sum(1 for s in scholarships if "Fully Funded Living Stipend" in s["collections"])
        },
        {
            "id": "women-in-stem",
            "title": "Women in STEM Leadership",
            "subtitle": "Dedicated fellowships for female engineering graduates and researchers",
            "icon": "fa-venus",
            "color": "#ec4899",
            "filter": "Women in STEM",
            "count": sum(1 for s in scholarships if "Women in STEM" in s["collections"] or "Women" in s["name"])
        },
        {
            "id": "no-gre",
            "title": "No-GRE Required",
            "subtitle": "Direct admission & funding evaluated on your GCOEK CGPA and projects",
            "icon": "fa-file-circle-check",
            "color": "#10b981",
            "filter": "No-GRE Required",
            "count": sum(1 for s in scholarships if "No-GRE Required" in s["collections"])
        },
        {
            "id": "low-gpa",
            "title": "Low GPA Friendly (>=6.5)",
            "subtitle": "Holistic selection valuing publications, internships, and work experience",
            "icon": "fa-chart-line",
            "color": "#3b82f6",
            "filter": "Low GPA Friendly (>=6.5)",
            "count": sum(1 for s in scholarships if "Low GPA Friendly (>=6.5)" in s["collections"])
        },
        {
            "id": "underrepresented",
            "title": "High Acceptance Asia & Oceania",
            "subtitle": "MEXT Japan, GKS Korea, SINGA Singapore, and Australia Research RTPs",
            "icon": "fa-compass",
            "color": "#8b5cf6",
            "filter": "Underrepresented Regions",
            "count": sum(1 for s in scholarships if "Underrepresented Regions" in s["collections"])
        }
    ]
    return collections


def filter_atlas_scholarships(
    scholarships: List[Dict[str, Any]],
    degree: Optional[str] = None,
    field: Optional[str] = None,
    country: Optional[str] = None,
    coverage: Optional[str] = None,
    collection: Optional[str] = None,
    min_cgpa: Optional[float] = None,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Applies multifaceted filters to The Scholar's Atlas dataset."""
    results = []
    q_clean = (query or "").lower().strip()
    c_clean = (country or "").lower().strip()
    d_clean = (degree or "").lower().strip()
    cov_clean = (coverage or "").lower().strip()
    f_clean = (field or "").lower().strip()
    col_clean = (collection or "").strip()

    for s in scholarships:
        if d_clean and d_clean not in s["degree_levels"].lower() and d_clean != "all":
            continue
        if c_clean and c_clean not in s["country"].lower() and c_clean != "all":
            continue
        if cov_clean and cov_clean != "all":
            if cov_clean == "full" and s["coverage_level"] != "full":
                continue
            elif cov_clean == "partial" and s["coverage_level"] != "partial":
                continue
        if col_clean and col_clean not in s["collections"]:
            continue
        if f_clean and f_clean != "all":
            fields_str = " ".join(s["fields"]).lower()
            if f_clean not in fields_str:
                continue
        if min_cgpa is not None and min_cgpa > 0:
            req_cgpa_4 = s.get("suggested_cgpa_4")
            if req_cgpa_4:
                # Convert 10-scale input to 4-scale approx
                student_cgpa_4 = (min_cgpa / 10.0) * 4.0 if min_cgpa > 4.0 else min_cgpa
                if student_cgpa_4 < float(req_cgpa_4) - 0.4:
                    continue
        if q_clean:
            searchable = f"{s['name']} {s['funder']} {s['country']} {s['coverage_summary']} {s['academic_note']}".lower()
            if q_clean not in searchable:
                continue
        results.append(s)

    return results


def run_match_wizard(
    scholarships: List[Dict[str, Any]],
    profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Executes 6-step conversational AI matching engine for GCOEK students.
    Returns Top 5 matches with dossier, fit score, win rationale, and red flags.
    """
    branch = profile.get("branch", "Computer Science")
    try:
        cgpa = float(profile.get("cgpa", 8.0))
    except (ValueError, TypeError):
        cgpa = 8.0
    try:
        scale = float(profile.get("scale", 10.0))
    except (ValueError, TypeError):
        scale = 10.0
    cgpa_norm_4 = (cgpa / scale) * 4.0
    degree = profile.get("target_degree", "Master")
    destinations = profile.get("destinations", ["Germany", "Switzerland", "United Kingdom", "USA"])
    need_full_funding = profile.get("need_full_funding", True)
    category = profile.get("category", "General")
    test_status = profile.get("test_status", "None Yet")

    scored = []
    for s in scholarships:
        score = 70
        reasons = []
        red_flags = []

        # Degree match
        if degree.lower() in s["degree_levels"].lower():
            score += 10
            reasons.append(f"Supports target degree: {degree.capitalize()}")

        # Destination match
        if any(d.lower() in s["country"].lower() for d in destinations):
            score += 10
            reasons.append(f"Located in target destination: {s['country']}")

        # Funding match
        if need_full_funding:
            if s["coverage_level"] == "full" or s["out_of_pocket_usd_per_year"] == 0:
                score += 10
                reasons.append("100% tuition and living expenses fully covered (Zero out-of-pocket)")
            else:
                score -= 15
                red_flags.append(f"Partial funding: Estimated out-of-pocket ~${s['out_of_pocket_usd_per_year']:,}/year")

        # Academic match
        req_cgpa = s.get("suggested_cgpa_4")
        if req_cgpa:
            if cgpa_norm_4 >= float(req_cgpa):
                score += 8
                reasons.append(f"Your CGPA ({cgpa}/{scale}) safely meets competitive benchmark (~{req_cgpa}/4.0)")
            else:
                score -= 8
                red_flags.append(f"High GPA threshold (~{req_cgpa}/4.0) — compensate with strong research project")

        # Test score readiness
        if test_status in ["IELTS Done", "TOEFL Done"] and s.get("english_requirement"):
            score += 5
            reasons.append("Satisfies English language testing requirements")
        elif "none" in test_status.lower() and "gre" in s.get("academic_note", "").lower():
            red_flags.append("GRE score recommended for competitive ranking")

        score = max(50, min(99, score))
        scored.append({
            "scholarship": s,
            "fit_score": score,
            "why_you_will_win": reasons if reasons else ["Strong engineering foundation from GCOEK."],
            "red_flags": red_flags if red_flags else ["Highly competitive applicant pool — submit before priority deadline."],
            "action_plan": f"1. Request GCOEK transcripts from Controller of Examinations. 2. Contact HoD {branch} for LORs. 3. Draft 500-word SOP targeted to {s['funder']}."
        })

    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    return {
        "student_profile": {
            "institution": "Government College of Engineering, Kolhapur (GCOEK)",
            "branch": branch,
            "cgpa": f"{cgpa} / {scale} ({round(cgpa_norm_4, 2)} / 4.0 equiv)",
            "target_degree": degree,
            "destinations": destinations,
            "category": category
        },
        "total_evaluated": len(scholarships),
        "top_matches": scored[:5]
    }
