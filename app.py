"""
Scholarship Finder for Government College of Engineering, Kolhapur
Web Server (Flask) - Multi-Page Application
"""
import os
import io
import uuid
from typing import Optional
from flask import Flask, render_template, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
import pandas as pd

import matching_service
import agent_service

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "gcoek-scholarship-finder-2026")
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

DEFAULT_DATASET = "europe_scholarships_matching.csv"
current_dataset_path = DEFAULT_DATASET
active_df: pd.DataFrame = matching_service.load_data(DEFAULT_DATASET)
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
    return {
        "COLLEGE_NAME": COLLEGE_NAME,
        "COLLEGE_TAGLINE": COLLEGE_TAGLINE,
        "DATASET_STATS": stats,
    }


# ================= MULTI-PAGE HTML ROUTES =================

@app.route("/")
def home():
    """Main Scholarship Directory and Matcher Page."""
    return render_template("index.html")


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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"=====================================================")
    print(f"  {COLLEGE_TAGLINE}")
    print(f"  Access locally at: http://127.0.0.1:{port}")
    print(f"  Active dataset: {current_dataset_path} ({len(active_df)} scholarships)")
    print(f"=====================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
