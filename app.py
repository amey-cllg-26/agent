"""
Scholarship Finder for Government College of Engineering, Kolhapur
Web Server (Flask) - Multi-Page Application
"""
import os
import io
import uuid
from typing import Optional
from flask import Flask, render_template, request, jsonify, send_file, abort, Response, redirect
from werkzeug.utils import secure_filename
import pandas as pd

import matching_service
import agent_service
import india_service
import atlas_service

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gcoek-scholarship-finder-2026")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DEFAULT_DATASET = "europe_scholarships_matching.csv"
current_dataset_path = DEFAULT_DATASET
active_df: pd.DataFrame = matching_service.load_data(DEFAULT_DATASET)
india_df: pd.DataFrame = india_service.load_india_data()
agent = agent_service.ScholarshipAgent()

COLLEGE_TAGLINE = "Scholarship Finder for Government College of Engineering, Kolhapur"
COLLEGE_NAME = "Government College of Engineering, Kolhapur"


def get_dataset_stats(df: pd.DataFrame, filename: str) -> dict:
    """Computes summary statistics for the active dataset."""
    countries = [c for c in df["country"].dropna().unique() if str(c).strip()]
    coverage_counts = df["coverage_level"].value_counts().to_dict() if "coverage_level" in df.columns else {}
    return {
        "filename": os.path.basename(filename),
        "total_scholarships": len(df),
        "countries_count": len(countries),
        "countries": sorted(list(set(countries))),
        "coverage_counts": {str(k): int(v) for k, v in coverage_counts.items()},
        "columns": list(df.columns)
    }


# Context processor to make institutional branding available in every template
@app.context_processor
def inject_institutional_branding():
    stats = get_dataset_stats(active_df, current_dataset_path)
    india_stats = india_service.get_india_stats(india_df)
    return {
        "COLLEGE_NAME": COLLEGE_NAME,
        "COLLEGE_TAGLINE": COLLEGE_TAGLINE,
        "DATASET_STATS": stats,
        "INDIA_STATS": india_stats,
    }


# ================= MULTI-PAGE HTML ROUTES =================

@app.route("/")
def home():
    """Main Scholarship Directory and Matcher Page (The Scholar's Atlas)."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    globe_dots = atlas_service.get_opportunity_globe_data(all_atlas)
    closing_soon = atlas_service.get_closing_soon_rail(all_atlas, limit=8)
    collections = atlas_service.get_featured_collections(all_atlas)
    return render_template(
        "index.html",
        atlas_scholarships=all_atlas,
        globe_dots=globe_dots,
        closing_soon=closing_soon,
        featured_collections=collections
    )


@app.route("/explore")
def explore_page():
    """The Scholar's Atlas: Multi-faceted Scholarship Discovery & Filters."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    collections = atlas_service.get_featured_collections(all_atlas)
    countries = sorted(list(set(s["country"] for s in all_atlas)))
    return render_template(
        "explore.html",
        scholarships=all_atlas,
        collections=collections,
        countries=countries
    )


@app.route("/scholarships/<slug>")
def scholarship_dossier_page(slug: str):
    """The Scholar's Atlas: Full Academic Dossier for a Scholarship Program."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    matched = next((s for s in all_atlas if s["slug"] == slug), None)
    if not matched:
        matched = next((s for s in all_atlas if slug in s["slug"] or s["slug"] in slug), None)
    if not matched:
        abort(404)
    similar = [
        s for s in all_atlas
        if s["slug"] != matched["slug"] and (s["country"] == matched["country"] or s["coverage_level"] == matched["coverage_level"])
    ][:3]
    return render_template("scholarship_detail.html", s=matched, similar=similar)


@app.route("/match")
def match_wizard_page():
    """The Scholar's Atlas: 6-Step Conversational AI Matching Questionnaire."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    countries = sorted(list(set(s["country"] for s in all_atlas)))
    return render_template("match.html", countries=countries)


@app.route("/deadlines")
def deadlines_page():
    """The Scholar's Atlas: Deadline Radar & Monthly Heatmap."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    return render_template("deadlines.html", scholarships=all_atlas)


@app.route("/tracker")
def tracker_page():
    """The Scholar's Atlas: Drag-and-Drop Application Pipeline (Kanban)."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    return render_template("tracker.html", scholarships=all_atlas)


@app.route("/profile")
def profile_page():
    """The Scholar's Atlas: Student Passport, Readiness Score & CGPA Converter."""
    return render_template("profile.html")


@app.route("/countries")
def countries_page():
    """Browse Scholarships by Destination Country and Region."""
    # Group scholarships by country
    country_groups = {}
    for _, row in active_df.iterrows():
        c = str(row.get("country", "Other")).strip()
        if c not in country_groups:
            country_groups[c] = []
        c_val = row.get("est_annual_cost_usd")
        s_val = row.get("est_annual_support_usd")
        cost = c_val if pd.notna(c_val) and c_val != "" else 0
        support = s_val if pd.notna(s_val) and s_val != "" else 0
        out_of_pocket = max(0, cost - support)
        country_groups[c].append(matching_service.row_to_dict(row, out_of_pocket, "target", []))

    sorted_countries = sorted(country_groups.keys())
    return render_template("countries.html", country_groups=country_groups, sorted_countries=sorted_countries)


@app.route("/dataset")
def dataset_page():
    """Dedicated Dataset Manager & Upload Page."""
    stats = get_dataset_stats(active_df, current_dataset_path)
    return render_template("dataset.html", stats=stats)


@app.route("/guide")
def guide_page():
    """Official GCOEK Engineering Higher Studies & Scholarships Guide."""
    return render_template("guide.html")


@app.route("/advisor")
def advisor_page():
    """Dedicated Scholarship Counseling & Advisor Desk."""
    return render_template("advisor.html")


@app.route("/scholarship/<path:name>")
def scholarship_detail_page(name: str):
    """Dedicated view for a single scholarship program."""
    import urllib.parse
    clean_name = urllib.parse.unquote(name).strip()
    matches = active_df[active_df["scholarship_name"].str.contains(clean_name, case=False, regex=False)]
    if matches.empty:
        # Fallback to key words search
        words = [w for w in clean_name.split() if len(w) > 3]
        for w in words:
            sub = active_df[active_df["scholarship_name"].str.contains(w, case=False, regex=False)]
            if not sub.empty:
                matches = sub
                break

    if matches.empty:
        abort(404)

    row = matches.iloc[0]
    c_val = row.get("est_annual_cost_usd")
    s_val = row.get("est_annual_support_usd")
    cost = c_val if pd.notna(c_val) and c_val != "" else 0
    support = s_val if pd.notna(s_val) and s_val != "" else 0
    out_of_pocket = max(0, cost - support)
    item = matching_service.row_to_dict(row, out_of_pocket, "target", [])

    return render_template("detail.html", scholarship=item)


@app.route("/india")
def india_page():
    """Dedicated Indian Caste & Category Scholarships Portal for GCOEK."""
    stats = india_service.get_india_stats(india_df)
    categories = ["All", "SC", "ST", "OBC", "VJNT", "SBC", "EBC / Open", "Minority", "PWD"]
    initial_schemes = india_service.filter_india_scholarships(india_df)
    return render_template("india.html", stats=stats, categories=categories, initial_schemes=initial_schemes[:30])


@app.route("/india/scheme/<int:scheme_id>")
def india_scheme_detail_page(scheme_id: int):
    """Dedicated view for an Indian Caste / Government Scholarship Scheme."""
    scheme = india_service.get_scheme_by_id(india_df, scheme_id)
    if not scheme:
        abort(404)
    raw_docs = scheme.get("required_documents", "")
    doc_list = [d.strip() for d in raw_docs.split(";") if d.strip()]
    return render_template("india_detail.html", scheme=scheme, doc_list=doc_list)


@app.route("/api/india/scholarships", methods=["GET", "POST"])
def api_india_scholarships():
    """API endpoint to search and filter Indian caste scholarships."""
    if request.method == "POST":
        data = request.get_json() or {}
        category = data.get("category", "All")
        max_income = data.get("max_income")
        authority = data.get("authority", "All")
        degree = data.get("degree", "All")
        keyword = data.get("keyword", "")
    else:
        category = request.args.get("category", "All")
        max_income_raw = request.args.get("income", "")
        max_income = float(max_income_raw) if max_income_raw else None
        authority = request.args.get("authority", "All")
        degree = request.args.get("degree", "All")
        keyword = request.args.get("q", "")

    results = india_service.filter_india_scholarships(
        india_df,
        category=category,
        max_income=max_income,
        authority=authority,
        degree=degree,
        keyword=keyword
    )
    return jsonify({
        "total": len(results),
        "results": results
    })


@app.route("/api/india/stats", methods=["GET"])
def api_india_stats():
    """Returns metadata and category statistics for Indian scholarships."""
    return jsonify(india_service.get_india_stats(india_df))


@app.route("/api/india/export", methods=["GET"])
def api_india_export():
    """Exports the Indian caste scholarships dataset as CSV."""
    return send_file(
        "india_caste_scholarships.csv",
        mimetype="text/csv",
        as_attachment=True,
        download_name="gcoek_india_caste_scholarships.csv"
    )



# ================= REST API ENDPOINTS =================

@app.route("/api/dataset-info", methods=["GET"])
def dataset_info():
    """Returns metadata for the currently active dataset."""
    stats = get_dataset_stats(active_df, current_dataset_path)
    return jsonify(stats)


@app.route("/api/scholarships", methods=["GET"])
def list_scholarships():
    """Returns list of scholarships with optional search and filtering."""
    query = request.args.get("q", "").strip().lower()
    country = request.args.get("country", "").strip().lower()
    degree = request.args.get("degree", "").strip().lower()
    coverage = request.args.get("coverage", "").strip().lower()

    filtered = active_df.copy()

    if degree:
        norm_deg = matching_service.normalize_degree(degree)
        if norm_deg:
            filtered = filtered[filtered["degree_levels"].str.lower().str.contains(norm_deg, na=False)]

    if country:
        filtered = filtered[filtered["country"].str.lower().str.contains(country, na=False)]

    if coverage and coverage != "all":
        filtered = filtered[filtered["coverage_level"].str.lower().str.contains(coverage, na=False)]

    if query:
        mask = (
            filtered["scholarship_name"].str.lower().str.contains(query, na=False) |
            filtered["funder"].str.lower().str.contains(query, na=False) |
            filtered["coverage_summary"].str.lower().str.contains(query, na=False) |
            filtered["academic_note"].str.lower().str.contains(query, na=False) |
            filtered["country"].str.lower().str.contains(query, na=False)
        )
        filtered = filtered[mask]

    results = []
    for _, row in filtered.iterrows():
        c_val = row.get("est_annual_cost_usd")
        s_val = row.get("est_annual_support_usd")
        cost = c_val if pd.notna(c_val) and c_val != "" else 0
        support = s_val if pd.notna(s_val) and s_val != "" else 0
        out_of_pocket = max(0, cost - support)
        results.append(matching_service.row_to_dict(row, out_of_pocket, "target", []))

    return jsonify({
        "total": len(results),
        "scholarships": results
    })


@app.route("/api/recommend", methods=["POST"])
def get_recommendations():
    """Computes personalized scholarship matches based on student profile."""
    data = request.get_json() or {}

    degree = data.get("degree", "master")
    try:
        cgpa = float(data.get("cgpa", 3.0))
        cgpa_scale = float(data.get("cgpa_scale", 4.0))
        budget_usd = float(data.get("budget_usd", 10000.0))
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric parameter: {e}"}), 400

    nationality = data.get("nationality")
    country = data.get("country")
    coverage = data.get("coverage")
    keyword = data.get("keyword")

    recommendations = matching_service.recommend(
        df=active_df,
        degree=degree,
        cgpa=cgpa,
        cgpa_scale=cgpa_scale,
        budget_usd=budget_usd,
        nationality=nationality,
        country=country,
        coverage=coverage,
        keyword=keyword
    )

    return jsonify(recommendations)


@app.route("/api/chat", methods=["POST"])
def chat_with_agent():
    """Communicates with the AI Scholarship Advisor."""
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))
    api_key_override = data.get("api_key", "").strip() or None

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    response = agent.chat(
        message=message,
        session_id=session_id,
        df=active_df,
        api_key_override=api_key_override
    )

    response["session_id"] = session_id
    return jsonify(response)


@app.route("/api/upload-dataset", methods=["POST"])
def upload_dataset():
    """Uploads a custom CSV dataset and sets it as the active dataset."""
    global active_df, current_dataset_path

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported."}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(save_path)

    try:
        new_df = matching_service.load_data(save_path)
        active_df = new_df
        current_dataset_path = save_path
        stats = get_dataset_stats(active_df, current_dataset_path)
        return jsonify({
            "message": f"Dataset '{filename}' successfully loaded ({len(active_df)} scholarships)!",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500


@app.route("/api/reset-dataset", methods=["POST"])
def reset_dataset():
    """Resets to default verified global scholarships dataset."""
    global active_df, current_dataset_path
    try:
        active_df = matching_service.load_data(DEFAULT_DATASET)
        current_dataset_path = DEFAULT_DATASET
        stats = get_dataset_stats(active_df, current_dataset_path)
        return jsonify({
            "message": f"Reset to default dataset successfully ({len(active_df)} scholarships).",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": f"Failed to reset dataset: {str(e)}"}), 500


@app.route("/api/export", methods=["GET"])
def export_dataset():
    """Exports active dataset as CSV."""
    buf = io.StringIO()
    active_df.to_csv(buf, index=False)
    mem = io.BytesIO()
    mem.write(buf.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="gcoek_scholarships_export.csv"
    )


@app.route("/api/atlas/scholarships", methods=["GET"])
def api_atlas_scholarships():
    """Dynamic API endpoint for filtering Scholar's Atlas data."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    deg = request.args.get("degree")
    fld = request.args.get("field")
    cntry = request.args.get("country")
    cov = request.args.get("coverage")
    col = request.args.get("collection")
    q = request.args.get("q")
    cgpa = request.args.get("cgpa", type=float)
    filtered = atlas_service.filter_atlas_scholarships(
        all_atlas, degree=deg, field=fld, country=cntry, coverage=cov, collection=col, min_cgpa=cgpa, query=q
    )
    return jsonify({"total": len(filtered), "scholarships": filtered})


@app.route("/api/match-wizard", methods=["POST"])
def api_match_wizard():
    """AI matching endpoint returning personalized student dossier."""
    data = request.get_json() or {}
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    dossier = atlas_service.run_match_wizard(all_atlas, data)
    return jsonify(dossier)


@app.route("/api/calendar/export.ics", methods=["GET"])
def export_calendar_ics():
    """Generates an iCalendar (.ics) file with verified scholarship deadlines."""
    all_atlas = atlas_service.load_atlas_scholarships(active_df)
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//GCOEK//Scholar Atlas//EN",
        "X-WR-CALNAME:GCOEK Scholarship Deadlines",
    ]
    for s in all_atlas:
        clean_name = s["name"].replace(",", "\\,")
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{clean_name} Deadline",
            f"DESCRIPTION:Scholarship: {clean_name}\\nFunder: {s['funder']}\\nCountry: {s['country']}\\nOfficial Website: {s['official_website']}",
            f"URL:{s['official_website']}",
            "DTSTART:20261130T090000Z",
            "DTEND:20261130T170000Z",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])
    ics_lines.append("END:VCALENDAR")
    return Response(
        "\r\n".join(ics_lines),
        mimetype="text/calendar",
        headers={"Content-Disposition": "attachment; filename=gcoek_scholarship_deadlines.ics"}
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"=====================================================")
    print(f"  {COLLEGE_TAGLINE}")
    print(f"  Access locally at: http://127.0.0.1:{port}")
    print(f"  Active dataset: {current_dataset_path} ({len(active_df)} scholarships)")
    print(f"=====================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
