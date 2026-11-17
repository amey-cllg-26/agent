"""
Matching service logic for the Scholarship Finder Agent.
Handles profile-based filtering, CGPA normalisation, budget arithmetic,
heuristic fit categorisation (Target, Safer, Reach), and custom dataset flexibility.
"""
from typing import Dict, Any, List, Optional
import os
import pandas as pd

DEADLINE_FALLBACK = "Not specified — verify on official site"
NOT_RECORDED = "Not recorded - check the official website"
FIT_ORDER = {"target": 0, "safer": 1, "reach": 2}


def format_deadline(val: Any) -> str:
    """Parses and formats a deadline value into a human-readable format.
    Never returns 0.0 or 0. Falls back to 'Not specified — verify on official site'.
    """
    if val is None or pd.isna(val):
        return DEADLINE_FALLBACK
    s = str(val).strip()
    if not s or s in ("0", "0.0", "nan", "None", "null", "<NA>", NOT_RECORDED):
        return DEADLINE_FALLBACK
    # If already a human-readable string (e.g. 'Opens Aug–Oct annually' or '15 Nov 2026'), return it
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt) and dt.year > 2000:
            return dt.strftime("%d %b %Y")
    except Exception:
        pass
    return s

# Column aliases to support diverse CSV datasets uploaded by users
COLUMN_ALIASES = {
    "scholarship_name": ["scholarship_name", "name", "title", "scholarship", "program_name"],
    "country": ["country", "location", "host_country", "destination"],
    "funder": ["funder", "organization", "institution", "provider", "university"],
    "degree_levels": ["degree_levels", "degree", "level", "target_degree", "study_level"],
    "coverage_level": ["coverage_level", "coverage", "type", "funding_type", "award_type"],
    "coverage_summary": ["coverage_summary", "benefits", "description", "details", "award_amount", "amount"],
    "min_grade_percent_official": ["min_grade_percent_official", "min_grade", "minimum_percentage", "min_percent"],
    "suggested_competitive_cgpa_4": ["suggested_competitive_cgpa_4", "competitive_cgpa", "target_cgpa", "min_cgpa", "cgpa"],
    "academic_note": ["academic_note", "academic_requirements", "academics", "requirements"],
    "english_requirement_note": ["english_requirement_note", "english_requirement", "language", "ielts_toefl"],
    "work_experience_note": ["work_experience_note", "work_experience", "experience"],
    "eligible_nationalities": ["eligible_nationalities", "nationality", "citizenship", "eligible_countries"],
    "est_annual_cost_usd": ["est_annual_cost_usd", "annual_cost", "cost_usd", "tuition_and_living_usd", "total_cost"],
    "est_annual_support_usd": ["est_annual_support_usd", "annual_support", "support_usd", "stipend_usd", "coverage_usd"],
    "competitiveness_estimate": ["competitiveness_estimate", "competitiveness", "acceptance_rate"],
    "deadline": ["deadline", "due_date", "application_deadline", "closing_date"],
    "official_website": ["official_website", "website", "link", "url", "apply_url"],
    "confidence": ["confidence", "data_confidence", "verification_status"]
}


def standardize_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names of any uploaded DataFrame to our standard schema."""
    df = raw_df.copy()
    rename_map = {}
    normalized_cols = {col: str(col).lower().strip().replace(" ", "_").replace("-", "_") for col in df.columns}

    # Match each standard column name against existing columns or aliases
    for std_name, aliases in COLUMN_ALIASES.items():
        found = False
        for col_orig, col_norm in normalized_cols.items():
            if col_norm in aliases:
                rename_map[col_orig] = std_name
                found = True
                break
        if not found and std_name not in df.columns:
            df[std_name] = ""

    df = df.rename(columns=rename_map)

    # Convert numeric fields
    for col in ["est_annual_cost_usd", "est_annual_support_usd", "suggested_competitive_cgpa_4"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = None

    # Text metadata columns that must NEVER be filled with numeric 0
    text_cols = [
        "scholarship_name", "country", "funder", "degree_levels", "coverage_level",
        "coverage_summary", "academic_note", "english_requirement_note",
        "work_experience_note", "eligible_nationalities", "competitiveness_estimate",
        "deadline", "official_website", "confidence", "min_grade_percent_official"
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["nan", "None", "0.0", "0", "<NA>"], "")

    # Fill remaining columns appropriately by dtype
    for col in df.columns:
        if col not in ["est_annual_cost_usd", "est_annual_support_usd", "suggested_competitive_cgpa_4"] and col not in text_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna("")

    return df


def load_data(path: str = "europe_scholarships_matching.csv") -> pd.DataFrame:
    """Loads and standardizes a scholarship dataset from a CSV path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset file not found at {path}")

    try:
        raw_df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        raw_df = pd.read_csv(path, encoding="latin1")

    return standardize_dataframe(raw_df)


def normalize_degree(text: Optional[str]) -> Optional[str]:
    """Maps various degree strings to bachelor, master, or phd."""
    t = (text or "").lower().strip()
    if not t:
        return None
    if any(k in t for k in ["phd", "doctor", "postdoc"]):
        return "phd"
    if any(k in t for k in ["master", "msc", "postgrad", "ma", "mba"]):
        return "master"
    if any(k in t for k in ["bachelor", "undergrad", "bsc", "ba"]):
        return "bachelor"
    return None


def to_cgpa_4(cgpa: float, scale: float):
    """Convert to an approximate 4.0 scale. Returns (value, note)."""
    if scale in (4, 4.0):
        return round(float(cgpa), 2), "Used as given (4.0 scale)."
    if scale in (5, 5.0, 10, 10.0):
        val = round(cgpa / scale * 4, 2)
        return val, f"Converted linearly from a {scale:g}-point scale; this is approximate."
    if scale == 100 or scale == 100.0:
        table = [(85, 4.0), (80, 3.7), (75, 3.3), (70, 3.0), (65, 2.7), (60, 2.3)]
        value = next((v for p, v in table if cgpa >= p), 2.0)
        return value, "Converted from a percentage using a standard bracket; approximate."
    val = round(cgpa / scale * 4, 2)
    return val, "Converted linearly; approximate."


def fit_label(cgpa_4: float, suggested: Optional[float]) -> str:
    """Categorizes fit into safer, target, or reach."""
    if suggested is None or pd.isna(suggested):
        return "target"
    gap = cgpa_4 - suggested
    if gap >= 0.2:
        return "safer"
    if gap >= -0.1:
        return "target"
    return "reach"


def get_gpa_requirement_text(row: pd.Series) -> str:
    """Returns human-readable minimum grade/CGPA requirement. Never returns ~0.0%."""
    official = str(row.get("min_grade_percent_official", "")).strip()
    if official and official not in ("0", "0.0", "nan", "None", "<NA>"):
        try:
            val = float(official)
            if val > 0:
                return f"Published minimum: ~{val:g}% (or equivalent in your institution's conversion)"
        except ValueError:
            return f"Published minimum: {official}"

    comp = row.get("suggested_competitive_cgpa_4")
    if pd.notna(comp):
        try:
            val4 = float(comp)
            if val4 > 0:
                val10 = round((val4 / 4.0) * 10, 1)
                return f"Suggested competitive CGPA: ~{val4} / 4.0 (Approx. {val10} / 10.0 GCOEK)"
        except (ValueError, TypeError):
            pass

    return "Published minimum: Not specified — verify how your institution converts CGPA to percentage."


def row_to_dict(row: pd.Series, out_of_pocket: float, fit: str, warnings: List[str]) -> Dict[str, Any]:
    """Transforms a DataFrame row into a standardized response dict."""
    return {
        "name": str(row.get("scholarship_name", "Unnamed Scholarship")),
        "country": str(row.get("country", "")),
        "funder": str(row.get("funder", "")),
        "fit": fit,
        "coverage_level": str(row.get("coverage_level", "unknown")),
        "coverage_summary": str(row.get("coverage_summary", "")),
        "est_annual_cost_usd": None if pd.isna(row.get("est_annual_cost_usd")) else int(row.get("est_annual_cost_usd")),
        "est_annual_support_usd": None if pd.isna(row.get("est_annual_support_usd")) else int(row.get("est_annual_support_usd")),
        "out_of_pocket_usd_per_year": int(out_of_pocket),
        "suggested_competitive_cgpa_4": None if pd.isna(row.get("suggested_competitive_cgpa_4")) else float(row.get("suggested_competitive_cgpa_4")),
        "gpa_requirement": get_gpa_requirement_text(row),
        "academic_note": str(row.get("academic_note", "")),
        "english_requirement": str(row.get("english_requirement_note", "")),
        "work_experience": str(row.get("work_experience_note", "")),
        "eligible_nationalities": str(row.get("eligible_nationalities", "")),
        "warnings": warnings,
        "deadline": format_deadline(row.get("deadline")),
        "official_website": str(row.get("official_website", "")),
        "data_confidence": str(row.get("confidence", "")),
        "last_verified": str(row.get("last_verified", "")).strip() if pd.notna(row.get("last_verified")) and str(row.get("last_verified", "")).strip() != "" else "November 2026",
    }


def recommend(
    df: pd.DataFrame,
    degree: str,
    cgpa: float,
    cgpa_scale: float = 4.0,
    budget_usd: float = 100000.0,
    nationality: Optional[str] = None,
    country: Optional[str] = None,
    coverage: Optional[str] = None,
    keyword: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    Filters and ranks scholarships based on degree, CGPA, budget, nationality, country, and keywords.
    """
    degree_n = normalize_degree(degree)
    if degree_n is None:
        return {"error": "Degree level not recognised. Please choose bachelor, master, or phd."}
    if cgpa_scale <= 0 or cgpa < 0 or cgpa > cgpa_scale:
        return {"error": f"CGPA ({cgpa}) must be between 0 and scale ({cgpa_scale})."}

    cgpa_4, conversion_note = to_cgpa_4(cgpa, cgpa_scale)
    results = []
    over_budget = []

    keyword_clean = (keyword or "").lower().strip()
    country_clean = (country or "").lower().strip()
    coverage_clean = (coverage or "").lower().strip()

    for _, row in df.iterrows():
        degrees_str = str(row.get("degree_levels", "")).lower()
        if degree_n not in degrees_str and degrees_str != "":
            continue

        if country_clean:
            row_country = str(row.get("country", "")).lower()
            if country_clean not in row_country:
                continue

        if coverage_clean and coverage_clean != "all":
            row_cov = str(row.get("coverage_level", "")).lower()
            if coverage_clean not in row_cov:
                continue

        if keyword_clean:
            searchable_fields = " ".join([
                str(row.get("scholarship_name", "")),
                str(row.get("funder", "")),
                str(row.get("coverage_summary", "")),
                str(row.get("academic_note", "")),
                str(row.get("country", "")),
                str(row.get("eligible_nationalities", "")),
            ]).lower()
            if keyword_clean not in searchable_fields:
                continue

        warnings = []

        # Published minimum grade check - only warn if valid positive percentage exists
        official = str(row.get("min_grade_percent_official", "")).strip()
        if official and official not in ("0", "0.0", "nan", "None", "<NA>"):
            try:
                min_pct = float(official)
                if min_pct > 0:
                    if cgpa_scale == 100:
                        if cgpa < min_pct:
                            continue
                    else:
                        warnings.append(
                            f"Published minimum: ~{min_pct:g}%. Verify how your institution converts CGPA to percentage."
                        )
            except ValueError:
                pass

        # Nationality check warning
        elig = str(row.get("eligible_nationalities", ""))
        if any(k in elig.lower() for k in ("only", "partner", "check", "income", "varies", "non-", "commonwealth")):
            who = f" (your nationality: {nationality})" if nationality else ""
            warnings.append(f"Check nationality requirements{who}: {elig}")

        cost = row.get("est_annual_cost_usd")
        support = row.get("est_annual_support_usd")
        c_val = cost if pd.notna(cost) and cost != "" else 0
        s_val = support if pd.notna(support) and support != "" else 0
        out_of_pocket = max(0, c_val - s_val)

        fit = fit_label(cgpa_4, row.get("suggested_competitive_cgpa_4"))
        item = row_to_dict(row, out_of_pocket, fit, warnings)

        if out_of_pocket <= budget_usd:
            results.append(item)
        else:
            over_budget.append(item)

    COVERAGE_ORDER = {"full": 0, "tuition": 1, "stipend": 2, "partial": 3, "unknown": 4}
    # Default sort: by fit (Target -> Safer -> Reach), then coverage (Fully Funded first), then out-of-pocket
    results.sort(key=lambda r: (
        FIT_ORDER.get(r.get("fit", "target"), 1),
        COVERAGE_ORDER.get(str(r.get("coverage_level", "")).lower(), 3),
        r.get("out_of_pocket_usd_per_year", 0),
        r.get("name", "")
    ))
    over_budget.sort(key=lambda r: (
        FIT_ORDER.get(r.get("fit", "target"), 1),
        r.get("out_of_pocket_usd_per_year", 0)
    ))

    # Count by fit
    fit_counts = {"target": 0, "safer": 0, "reach": 0}
    for r in results:
        f = r.get("fit", "target")
        if f in fit_counts:
            fit_counts[f] += 1

    out = {
        "student_cgpa_4_used": cgpa_4,
        "conversion_note": conversion_note,
        "budget_usd_per_year": budget_usd,
        "total_matched": len(results),
        "fit_counts": fit_counts,
        "results": results[:limit],
        "note": "Costs, support amounts, and fit tags are heuristic estimations. Always verify on official websites.",
    }
    if not results:
        out["closest_but_over_budget"] = over_budget[:5]
    elif len(over_budget) > 0:
        out["closest_but_over_budget"] = over_budget[:3]

    return out
