"""
Agent service for the Scholarship Finder Web Application.
Supports Google Gemini via google-genai SDK when an API key is provided,
and provides an intelligent rule-based fallback advisor when running offline or without an API key.
"""
import os
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from dotenv import load_dotenv

import matching_service

load_dotenv()

SYSTEM_PROMPT = """You are the official Scholarship Advisor for Government College of Engineering, Kolhapur (GCOEK), an autonomous institute of the Government of Maharashtra.
Your tagline: "Scholarship Finder for Government College of Engineering, Kolhapur".

Your goal is to assist GCOEK engineering students (Computer Science, Mechanical, Civil, Electrical, and ENTC) and alumni in discovering:
1. **Indian Caste & Government Schemes**: MahaDBT Maharashtra Government schemes (SC Post-Matric, ST Post-Matric, OBC/VJNT/SBC Post-Matric & Freeship, Rajarshi Shahu Maharaj EBC 50% tuition waiver for Open/EWS <= 8 LPA, Dr. Panjabrao Deshmukh hostel allowance, Swadhar & Swayam yojna, Minority scholarships, Divyangjan/PWD schemes) and Central Schemes (AICTE Pragati for Girls, Saksham, Swanath, NSP Central Sector, ONGC, Siemens, FFE).
2. **International & Overseas Higher Studies Scholarships**: Global programs across USA, Europe, UK, Japan, Singapore, Australia, Canada, Middle East for B.E. internships (e.g. DAAD WISE), Master's (M.S./M.Tech), and Ph.D. degrees.

Instructions:
1. For Indian schemes, clearly state:
   - Reserved Category: SC, ST, OBC, VJNT, SBC, EBC/Open, Minority, PWD
   - Annual Family Income Limit (e.g. ₹2.5 LPA for SC/ST, ₹1 LPA for OBC scholarship / ₹8 LPA for Freeship, ₹8 LPA for EBC)
   - Assistance: 100% Tuition Fee Waiver, 50% Tuition Fee Waiver, Exam Fee, Maintenance, or Hostel Allowance
   - Mandatory Documents: Caste Certificate, Caste Validity Certificate, Tahsildar Income Certificate, Domicile of Maharashtra, Non-Creamy Layer (for OBC/VJNT/SBC), CAP Allotment Letter
   - Official Application Portal (e.g. MahaDBT: https://mahadbt.maharashtra.gov.in/ or NSP: https://scholarships.gov.in/)
2. Note that GCOEK uses a 10.0 CGPA scale (Shivaji University / DBATU standard: 8.0/10 ~ 3.2/4.0; 8.5/10 ~ 3.4/4.0; 9.0/10 ~ 3.6/4.0).
3. Group overseas recommendations into:
   - 🎯 Target: Realistic academic fit
   - 🛡️ Safer: Academic profile exceeds competitive threshold
   - 🚀 Reach: Highly selective / premier prestigious programs
4. Never invent fictional scholarships. Remind the student to verify exact deadlines and guidelines on the official portal before applying."""




class FallbackAdvisor:
    """Smart fallback advisor when Gemini API key is not present or offline."""

    def __init__(self):
        # In-memory session state for conversational extraction
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "degree": None,
                "cgpa": None,
                "scale": 10.0,
                "budget": None,
                "nationality": "India",
                "country": None,
                "history": [],
            }
        return self.sessions[session_id]

    def extract_entities(self, text: str, state: Dict[str, Any]):
        t = text.lower()

        # Degree extraction
        if any(w in t for w in ["phd", "ph.d", "doctorate", "doctoral"]):
            state["degree"] = "phd"
        elif any(w in t for w in ["master", "masters", "msc", "m.sc", "m.tech", "mtech", "ms", "m.s.", "postgrad", "mba"]):
            state["degree"] = "master"
        elif any(w in t for w in ["bachelor", "bachelors", "undergrad", "bsc", "b.sc", "b.e", "b.tech", "btech", "internship", "wise", "3rd year"]):
            state["degree"] = "bachelor"

        # CGPA extraction
        # Look for patterns like "cgpa 3.5", "gpa of 3.8", "3.4 out of 4", "85%", "78 out of 100"
        pct_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*(?:%|percent)", t)
        if pct_match:
            state["cgpa"] = float(pct_match.group(1))
            state["scale"] = 100.0
        else:
            scale_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:out of|/)\s*(4|5|10|100)", t)
            if scale_match:
                state["cgpa"] = float(scale_match.group(1))
                state["scale"] = float(scale_match.group(2))
            else:
                cgpa_match = re.search(r"(?:cgpa|gpa|grade|score)\s*(?:is|of|:)?\s*(\d+(?:\.\d+)?)", t)
                if cgpa_match:
                    val = float(cgpa_match.group(1))
                    state["cgpa"] = val
                    if val > 10:
                        state["scale"] = 100.0
                    elif val > 5:
                        state["scale"] = 10.0
                    elif val > 4:
                        state["scale"] = 5.0
                    else:
                        state["scale"] = 4.0

        # Budget extraction
        # Look for "$5000", "5000 usd", "budget 2000", "zero budget", "fully funded"
        if "fully funded" in t or "zero budget" in t or "no budget" in t or "0 budget" in t:
            state["budget"] = 0.0
        else:
            budget_match = re.search(r"(?:\$|usd\s*|budget\s*(?:of|is)?\s*)(\d[\d,.]*)(?:\s*usd|\s*dollars|\s*\$)?", t)
            if budget_match:
                raw_b = budget_match.group(1).replace(",", "")
                try:
                    state["budget"] = float(raw_b)
                except ValueError:
                    pass

        # Country / destination extraction
        countries_map = {
            "united states": "United States", "usa": "United States", "us": "United States", "america": "United States",
            "canada": "Canada", "australia": "Australia", "new zealand": "New Zealand",
            "united kingdom": "United Kingdom", "uk": "United Kingdom", "britain": "United Kingdom",
            "germany": "Germany", "france": "France", "sweden": "Sweden", "netherlands": "Netherlands",
            "switzerland": "Switzerland", "japan": "Japan", "south korea": "South Korea", "korea": "South Korea",
            "singapore": "Singapore", "china": "China", "taiwan": "Taiwan", "saudi arabia": "Saudi Arabia",
            "qatar": "Qatar", "turkey": "Turkey", "hungary": "Hungary", "italy": "Italy",
            "czech republic": "Czech Republic", "austria": "Austria", "finland": "Finland",
            "norway": "Norway", "denmark": "Denmark", "spain": "Spain", "ireland": "Ireland", "belgium": "Belgium"
        }
        for k, v in countries_map.items():
            if re.search(r"\b" + re.escape(k) + r"\b", t):
                state["country"] = v
                break

        # Nationality extraction (e.g., "from Bangladesh", "Indian student", "citizen of Nigeria")
        nat_match = re.search(r"(?:from|nationality|citizen(?:ship)? of)\s+([a-zA-Z\s]+?)(?:[.,;]|\band\b|$)", t)
        if nat_match:
            nat = nat_match.group(1).strip()
            if len(nat) > 2 and nat.lower() not in ["europe", "here", "today", "now"]:
                state["nationality"] = nat.title()

    def respond(self, message: str, session_id: str, df: pd.DataFrame) -> Dict[str, Any]:
        state = self.get_or_create_session(session_id)
        self.extract_entities(message, state)

        # Check for Indian caste / MahaDBT / Government scheme inquiry
        t_msg = message.lower()
        if any(w in t_msg for w in ["mahadbt", "caste", "ebc", "obc", "vjnt", "sbc", "swadhar", "swayam", "freeship", "pragati", "panjabrao", "minority"]):
            try:
                import india_service
                ind_df = india_service.load_india_data()
                kw = None
                cat = "All"
                if "sc" in t_msg: cat = "SC"
                elif "st" in t_msg: cat = "ST"
                elif "obc" in t_msg: cat = "OBC"
                elif "vjnt" in t_msg or "nt" in t_msg: cat = "VJNT"
                elif "sbc" in t_msg: cat = "SBC"
                elif "ebc" in t_msg or "ews" in t_msg: cat = "EBC / Open"
                elif "minority" in t_msg: cat = "Minority"
                elif "pwd" in t_msg or "disab" in t_msg: cat = "PWD"

                schemes = india_service.filter_india_scholarships(ind_df, category=cat, keyword=kw)
                if schemes:
                    top_items = schemes[:4]
                    items_txt = ""
                    for s in top_items:
                        inc_str = f"Up to ₹{s['max_income_inr']:,}/yr" if s['max_income_inr'] > 0 else "No Income Bar / Merit Based"
                        items_txt += f"### 🏛️ [{s['scheme_name']}](/india/scheme/{s['id']})\n"
                        items_txt += f"- **Authority**: {s['state_or_central']} • *{s['department']}*\n"
                        items_txt += f"- **Category**: `{s['caste_category']}` | **Income Limit**: {inc_str}\n"
                        items_txt += f"- **Benefit**: {s['benefit_summary']}\n"
                        items_txt += f"- **Key Documents**: {s['required_documents']}\n\n"

                    reply_text = (
                        f"## 🇮🇳 Government of Maharashtra (MahaDBT) & Central Schemes for GCOEK\n\n"
                        f"Here are the top scholarship schemes for **{cat}** students at Government College of Engineering, Kolhapur:\n\n"
                        f"{items_txt}"
                        f"👉 You can explore all 100+ state and central schemes on our dedicated **[🇮🇳 India & Caste Schemes Portal](/india)**."
                    )
                    return {
                        "reply": reply_text,
                        "matched_scholarships": [],
                        "session_state": state
                    }
            except Exception as e:
                pass

        # Check for scholarship detail inquiry (e.g., "tell me about DAAD", "info on Chevening")
        detail_match = re.search(r"(?:about|detail(?:s)? of|tell me about|info on)\s+([a-zA-Z\s]+)", message, re.IGNORECASE)
        if detail_match:
            query = detail_match.group(1).strip()
            matches = df[df["scholarship_name"].str.contains(query, case=False, regex=False)]
            if not matches.empty:
                r = matches.iloc[0]
                text = (
                    f"### 🎓 **{r['scholarship_name']}** ({r['country']})\n\n"
                    f"- **Funder**: {r.get('funder', 'N/A')}\n"
                    f"- **Degree Levels**: {r.get('degree_levels', 'N/A')}\n"
                    f"- **Coverage Level**: {r.get('coverage_level', '').title()}\n"
                    f"- **Benefits**: {r.get('coverage_summary', 'N/A')}\n"
                    f"- **Estimated Annual Cost**: ${r.get('est_annual_cost_usd', 0):,}\n"
                    f"- **Estimated Annual Support**: ${r.get('est_annual_support_usd', 0):,}\n"
                    f"- **Academic Note**: {r.get('academic_note', 'N/A')}\n"
                    f"- **Language Requirement**: {r.get('english_requirement_note', 'N/A')}\n"
                    f"- **Work Experience**: {r.get('work_experience_note', 'N/A')}\n"
                    f"- **Eligible Nationalities**: {r.get('eligible_nationalities', 'Check website')}\n"
                    f"- **Deadline**: {r.get('deadline') or matching_service.NOT_RECORDED}\n\n"
                    f"👉 [Visit Official Website]({r.get('official_website', '#')})"
                )
                return {
                    "reply": text,
                    "matched_scholarships": [matching_service.row_to_dict(r, 0, "target", [])],
                    "session_state": state
                }

        # Check if we have sufficient info to recommend
        missing = []
        if not state["degree"]:
            missing.append("your target degree level (Bachelor, Master, or PhD)")
        if state["cgpa"] is None:
            missing.append("your CGPA or percentage (and what scale it is on, e.g., 3.4/4.0 or 80%)")
        if state["budget"] is None:
            missing.append("your annual out-of-pocket budget in USD (e.g., $0 for fully-funded or $3,000)")
        if not state["nationality"]:
            missing.append("your nationality / citizenship")

        if missing:
            prompt_q = "To give you precise scholarship recommendations, could you please share " + missing[0] + "?"
            if len(missing) > 1:
                prompt_q += f" *(We will also need: {', '.join(missing[1:])})*"
            return {
                "reply": f"Hello! I am your Scholarship Advisor Agent. {prompt_q}",
                "matched_scholarships": [],
                "session_state": state
            }

        # We have all criteria! Run recommendation
        rec = matching_service.recommend(
            df=df,
            degree=state["degree"],
            cgpa=state["cgpa"],
            cgpa_scale=state["scale"],
            budget_usd=state["budget"],
            nationality=state["nationality"],
            country=state["country"]
        )

        results = rec.get("results", [])
        over_budget = rec.get("closest_but_over_budget", [])

        # Build response markdown
        cgpa_info = f"{state['cgpa']} ({rec.get('conversion_note', '')})"
        budget_info = f"${int(state['budget']):,} USD/year"
        nat_info = state["nationality"] or "Any"
        country_info = state["country"] or "Europe / Anywhere"

        lines = [
            f"### 🎯 Personalized Scholarship Matches",
            f"**Profile**: {state['degree'].title()} | CGPA: {cgpa_info} | Budget: {budget_info} | Nationality: {nat_info} | Preferred Country: {country_info}\n"
        ]

        if not results:
            lines.append("⚠️ **No scholarships completely matched your criteria within your budget.**")
            if over_budget:
                lines.append("\nHere are the **closest scholarships just over your budget**:\n")
                for s in over_budget[:3]:
                    lines.append(
                        f"- **{s['name']}** ({s['country']}) — Out-of-pocket: ~${s['out_of_pocket_usd_per_year']:,}/yr | [Official Link]({s['official_website']})"
                    )
        else:
            # Group into Target, Safer, Reach
            targets = [r for r in results if r["fit"] == "target"]
            safers = [r for r in results if r["fit"] == "safer"]
            reaches = [r for r in results if r["fit"] == "reach"]

            if targets:
                lines.append(f"\n#### 🎯 Target Matches ({len(targets)})")
                for s in targets[:4]:
                    lines.append(
                        f"- **[{s['name']}]({s['official_website']})** ({s['country']}): {s['coverage_summary']} | Out-of-pocket: **${s['out_of_pocket_usd_per_year']:,}/yr**"
                    )
            if safers:
                lines.append(f"\n#### 🛡️ Safer Options ({len(safers)})")
                for s in safers[:3]:
                    lines.append(
                        f"- **[{s['name']}]({s['official_website']})** ({s['country']}): {s['coverage_summary']} | Out-of-pocket: **${s['out_of_pocket_usd_per_year']:,}/yr**"
                    )
            if reaches:
                lines.append(f"\n#### 🚀 Reach / Highly Competitive ({len(reaches)})")
                for s in reaches[:3]:
                    lines.append(
                        f"- **[{s['name']}]({s['official_website']})** ({s['country']}): {s['coverage_summary']} | Out-of-pocket: **${s['out_of_pocket_usd_per_year']:,}/yr**"
                    )

            lines.append("\n> 💡 *Note: Costs, support values, and fit categories are heuristic estimates. Always verify exact deadlines and criteria on the official website before applying!*")

        return {
            "reply": "\n".join(lines),
            "matched_scholarships": results[:10],
            "session_state": state
        }


fallback_advisor = FallbackAdvisor()


class ScholarshipAgent:
    """Agent orchestrator supporting Gemini GenAI or FallbackAdvisor."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model = os.getenv("MODEL", "gemini-2.5-flash")
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Gemini Client: {e}")
                self.client = None

    def chat(self, message: str, session_id: str, df: pd.DataFrame, api_key_override: Optional[str] = None) -> Dict[str, Any]:
        effective_key = api_key_override or self.api_key or os.getenv("GEMINI_API_KEY")

        if effective_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=effective_key)

                # Define tools connected to the current DataFrame
                def recommend_scholarships(
                    degree: str,
                    cgpa: float,
                    cgpa_scale: float = 4.0,
                    budget_usd: float = 100000.0,
                    nationality: Optional[str] = None,
                    country: Optional[str] = None,
                ) -> dict:
                    return matching_service.recommend(df, degree, cgpa, cgpa_scale, budget_usd, nationality, country)

                def get_scholarship_details(name: str) -> dict:
                    r = df[df["scholarship_name"].str.contains(name, case=False, regex=False)]
                    if r.empty:
                        return {"error": f"No scholarship found matching '{name}'"}
                    return {k: (v if v == v else None) for k, v in r.iloc[0].to_dict().items()}

                response = client.models.generate_content(
                    model=self.model,
                    contents=message,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        tools=[recommend_scholarships, get_scholarship_details],
                    )
                )

                reply_text = response.text or "I reviewed your profile with our scholarship matching tools."
                return {
                    "reply": reply_text,
                    "matched_scholarships": [],
                    "model_used": self.model,
                    "engine": "gemini"
                }
            except Exception as e:
                print(f"Gemini API error, using fallback: {e}")
                # Fall back gracefully to the rule-based agent
                res = fallback_advisor.respond(message, session_id, df)
                res["engine"] = "fallback"
                res["fallback_reason"] = str(e)
                return res

        # Offline / no API key: use smart rule-based fallback advisor
        res = fallback_advisor.respond(message, session_id, df)
        res["engine"] = "rule_based"
        return res
