"""
India Caste & Category-Based Scholarships Service
Provides loading, filtering, income validation, and statistics for
Government of Maharashtra (MahaDBT), Central (NSP), AICTE, and PSU schemes.
"""
import os
from typing import Dict, Any, List, Optional
import pandas as pd

DEFAULT_INDIA_DATASET = "india_caste_scholarships.csv"


def load_india_data(path: str = DEFAULT_INDIA_DATASET) -> pd.DataFrame:
    """Loads and standardizes the Indian caste scholarships dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Indian scholarships dataset not found at {path}")

    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin1")

    # Clean numeric columns
    df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)
    df["max_income_inr"] = pd.to_numeric(df["max_income_inr"], errors="coerce").fillna(0).astype(int)
    df["estimated_annual_benefit_inr"] = pd.to_numeric(df["estimated_annual_benefit_inr"], errors="coerce").fillna(0).astype(int)

    # String cleanup
    for col in ["scheme_name", "state_or_central", "department", "caste_category", "degree_level", "benefit_summary", "eligibility_criteria", "required_documents", "official_portal_url", "type", "description"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df


def filter_india_scholarships(
    df: pd.DataFrame,
    category: Optional[str] = None,
    max_income: Optional[float] = None,
    authority: Optional[str] = None,
    degree: Optional[str] = None,
    keyword: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filters Indian scholarships based on caste/category, income threshold, authority, and keyword.
    """
    filtered = df.copy()

    # Category filter
    if category and category.lower() != "all":
        cat_lower = category.lower().strip()
        # Matches specific caste or general 'all' open schemes if requested
        if cat_lower == "sc":
            filtered = filtered[filtered["caste_category"].str.lower().isin(["sc", "all"])]
        elif cat_lower == "st":
            filtered = filtered[filtered["caste_category"].str.lower().isin(["st", "all"])]
        elif cat_lower == "obc":
            filtered = filtered[filtered["caste_category"].str.lower().isin(["obc", "all"])]
        elif cat_lower in ["vjnt", "nt", "vj"]:
            filtered = filtered[filtered["caste_category"].str.lower().isin(["vjnt", "vjnt / sbc", "all"])]
        elif cat_lower == "sbc":
            filtered = filtered[filtered["caste_category"].str.lower().isin(["sbc", "vjnt / sbc", "all"])]
        elif cat_lower in ["ebc", "ews", "open", "sebc"]:
            filtered = filtered[filtered["caste_category"].str.lower().isin(["ebc / open", "all"])]
        elif cat_lower == "minority":
            filtered = filtered[filtered["caste_category"].str.lower().isin(["minority", "all"])]
        elif cat_lower in ["pwd", "disabled", "divyangjan"]:
            filtered = filtered[filtered["caste_category"].str.lower().isin(["pwd", "all"])]
        else:
            filtered = filtered[filtered["caste_category"].str.lower().str.contains(cat_lower, na=False)]

    # Income filter
    if max_income is not None and max_income > 0:
        # A scheme is eligible if it has no income limit (0) or student income <= max_income_inr
        filtered = filtered[(filtered["max_income_inr"] == 0) | (filtered["max_income_inr"] >= max_income)]

    # Authority filter (Maharashtra MahaDBT vs Central NSP vs Corporate)
    if authority and authority.lower() != "all":
        auth_lower = authority.lower()
        if "maha" in auth_lower or "state" in auth_lower:
            filtered = filtered[filtered["state_or_central"].str.lower().str.contains("maharashtra", na=False)]
        elif "central" in auth_lower or "nsp" in auth_lower or "aicte" in auth_lower:
            filtered = filtered[filtered["state_or_central"].str.lower().str.contains("central", na=False)]
        elif "corporate" in auth_lower or "private" in auth_lower or "psu" in auth_lower:
            filtered = filtered[filtered["state_or_central"].str.lower().str.contains("corporate|psu|private", na=False)]

    # Degree filter
    if degree and degree.lower() != "all":
        deg_lower = degree.lower()
        filtered = filtered[filtered["degree_level"].str.lower().str.contains(deg_lower, na=False)]

    # Keyword search
    if keyword and keyword.strip():
        kw = keyword.lower().strip()
        mask = (
            filtered["scheme_name"].str.lower().str.contains(kw, na=False) |
            filtered["department"].str.lower().str.contains(kw, na=False) |
            filtered["description"].str.lower().str.contains(kw, na=False) |
            filtered["benefit_summary"].str.lower().str.contains(kw, na=False) |
            filtered["caste_category"].str.lower().str.contains(kw, na=False)
        )
        filtered = filtered[mask]

    return filtered.to_dict(orient="records")


def get_scheme_by_id(df: pd.DataFrame, scheme_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a specific Indian scheme by its ID."""
    match = df[df["id"] == scheme_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def get_india_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes statistical breakdown of Indian scholarships."""
    categories = df["caste_category"].value_counts().to_dict()
    authorities = df["state_or_central"].value_counts().to_dict()
    departments = df["department"].value_counts().head(8).to_dict()

    return {
        "total_schemes": len(df),
        "categories": categories,
        "authorities": authorities,
        "departments": departments,
        "mahadbt_count": sum(count for auth, count in authorities.items() if "maharashtra" in auth.lower()),
        "central_count": sum(count for auth, count in authorities.items() if "central" in auth.lower()),
        "corporate_count": sum(count for auth, count in authorities.items() if "corporate" in auth.lower() or "private" in auth.lower() or "psu" in auth.lower())
    }
