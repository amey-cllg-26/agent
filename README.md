# 🎓 Scholarship Finder (Web Application)

An intelligent, full-stack web application running on `localhost:5000` that matches students with international and European scholarships based on their academic profile, budget, degree level, and nationality.

The platform allows you to **provide any scholarship dataset (CSV)** and perform **targeted, real-time matching** with automated GPA scale conversion, net out-of-pocket budget arithmetic, and competitiveness classification (Target, Safer, Reach).

---

## 🌟 Key Features

### 1. 📂 Flexible Dataset Management ("Dataset In -> Search Out")
- **Preloaded European Dataset**: Comes pre-configured with 20 curated European funding programs ([`europe_scholarships_matching.csv`](europe_scholarships_matching.csv)) including DAAD, Chevening, Gates Cambridge, Stipendium Hungaricum, Turkiye Burslari, and Erasmus Mundus.
- **Upload Any Custom CSV**: Drag-and-drop or browse your own CSV dataset directly from the web interface. The parser automatically normalizes column aliases (e.g. `scholarship_name`, `country`, `annual_cost`, `stipend`, etc.).
- **Live Dataset Statistics**: Instant summary of total records, host countries represented, and full vs. partial funding breakdown.
- **Export & Revert**: One-click download of the active dataset as a CSV or instant rollback to the default dataset.

### 2. 🔍 Precision Academic Search & Matching Engine
- **Target Degree**: Filter by Bachelor, Master, or PhD / Doctorate.
- **Multi-Scale GPA Normalizer**: Accepts GPA on 4.0, 5.0, 10.0, or 0–100% percentage scales, automatically calculating the approximate US 4.0 equivalent.
- **Net Out-of-Pocket Budget Filter**: Accurately computes `max(0, Est. Cost - Est. Support)` to guarantee your annual budget is strictly respected.
- **Nationality & Eligibility Verification**: Flags regional eligibility requirements and exclusions based on your citizenship.
- **Fit Categorization**:
  - **🎯 Target**: Balanced academic fit and competitiveness.
  - **🛡️ Safer**: Your academic profile comfortably exceeds suggested competitive thresholds.
  - **🚀 Reach**: Highly competitive, prestigious programs.
  - **Closest Over Budget**: Highlights strong academic matches that slightly exceed your current budget cap.

### 3. 🖥️ Professional, Authentic Interface
- Clean, high-contrast academic design built with modern CSS (no artificial AI template clichés or neon gradients).
- **Dual View Modes**: Switch seamlessly between **Grid Cards View** and a **Compact Table View**.
- **Scholarship Detail Modal**: Inspect full records including language prerequisites, work experience requirements, deadlines, and official direct application links.

### 4. 🤖 Scholarship Advisor Assistant
- Unobtrusive slide-over drawer accessible from the top navigation.
- **Dual Mode**:
  - **Offline Expert Advisor**: Automatically extracts student criteria across multi-turn queries, guides missing parameters, and performs instant database lookups.
  - **Google Gemini API**: Optional integration via `GEMINI_API_KEY` for LLM-powered conversational reasoning and advice.

---

## 📁 Project Structure

```text
c:\Users\HP\Downloads\agent\
├── app.py                            # Flask web server & REST API endpoints
├── matching_service.py               # Dataset standardizer, GPA converter & matching algorithms
├── agent_service.py                  # Dual-engine advisor (Gemini + offline rule-based advisor)
├── europe_scholarships_matching.csv  # Default European scholarship dataset
├── run.bat                           # 1-click Windows launcher (starts server & opens browser)
├── requirements.txt                  # Python dependencies
├── test_app.py                       # Automated test suite (14 unit & integration tests)
├── .env.example                      # Configuration template
├── uploads/                          # Custom uploaded CSV storage
├── templates/
│   └── index.html                    # Responsive Single-Page Application interface
└── static/
    ├── css/
    │   └── style.css                 # Clean, modern stylesheet
    └── js/
        └── app.js                    # Client-side filtering, dataset manager & modal controller
```

---

## 🚀 Quick Start Guide

### Option 1: One-Click Launcher (Windows)
Double-click [`run.bat`](run.bat). It will automatically:
1. Initialize the Python virtual environment (`.venv`).
2. Install any required dependencies.
3. Start the Flask server on `http://127.0.0.1:5000`.
4. Open your default web browser to the application.

---

### Option 2: Manual Terminal Setup

1. **Create and activate a virtual environment**:
   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **(Optional) Configure Gemini API**:
   Create a `.env` file from the example:
   ```powershell
   copy .env.example .env
   ```
   Add your Gemini API key (optional; the app works completely offline without it):
   ```env
   GEMINI_API_KEY=your_api_key_here
   PORT=5000
   ```

4. **Start the application**:
   ```powershell
   python app.py
   ```

5. **Open in browser**:
   Navigate to **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 📊 Dataset CSV Format Specification

When uploading your own dataset via the **Manage Dataset** modal, standard columns will be mapped automatically:

| Column Name | Description | Example |
| :--- | :--- | :--- |
| `scholarship_name` | Name of the scholarship program | `DAAD EPOS Scholarships` |
| `country` | Host country | `Germany` |
| `funder` | Organization or university providing funding | `DAAD` |
| `degree_levels` | Supported degree levels (semicolon-separated) | `master;phd` |
| `coverage_level` | Funding coverage type | `full` or `partial` |
| `coverage_summary` | Summary of what is covered | `Tuition, monthly stipend, health insurance` |
| `est_annual_cost_usd` | Estimated total annual living & tuition costs (USD) | `13000` |
| `est_annual_support_usd`| Estimated total annual scholarship award (USD) | `13000` |
| `suggested_competitive_cgpa_4` | Competitive academic GPA benchmark (4.0 scale) | `3.3` |
| `academic_note` | Academic degree requirements | `Relevant bachelor degree with strong grades` |
| `english_requirement_note` | Language test requirement | `IELTS 6.5 or TOEFL 90` |
| `work_experience_note` | Work or professional experience requirement | `At least 2 years of work experience` |
| `eligible_nationalities` | Eligible nationalities or restrictions | `Eligible developing countries only` |
| `deadline` | Application closing date | `October 31, 2026` |
| `official_website` | Link to official application website | `https://www.daad.de/en/` |

> *Note: Flexible aliases like `name`, `cost_usd`, `support_usd`, `website`, etc. are automatically recognized by `matching_service.py`.*

---

## 🧪 Running Automated Tests

Run the complete test suite using `pytest`:
```powershell
.\.venv\Scripts\pytest -v
```

All 14 tests verify:
- Web homepage and static asset rendering.
- Dataset statistics calculation and metadata retrieval.
- Profile matching logic (degree exclusions, GPA conversions, and budget limits).
- Multi-turn AI chat and entity extraction.
- Custom CSV upload, validation, and reset workflows.

---

## 📜 License
MIT License. Inspired by and built upon the core matching concepts from [Shadia09/Scholarship-Finder-Agent](https://github.com/Shadia09/Scholarship-Finder-Agent).
