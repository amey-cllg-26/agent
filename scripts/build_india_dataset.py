"""
Build standardized Indian Caste & Category Scholarships Dataset
Integrates Scholar-Spot, MahaDBT, NSP, and Flagship Engineering schemes.
"""
import os
import re
import pandas as pd

RAW_STEP_FILE = r"C:\Users\HP\.gemini\antigravity\brain\b43df9ca-7d88-44a2-9830-28a42a3d2906\.system_generated\steps\411\content.md"

def clean_cat(cat_str):
    c = str(cat_str).strip().lower()
    if "sc or nb" in c or "sc" in c:
        return "SC"
    if "st" in c:
        return "ST"
    if "vjnt or sbc" in c or "vj or nt or sbc" in c:
        return "VJNT / SBC"
    if "vjnt" in c or "dnt" in c:
        return "VJNT"
    if "sbc" in c:
        return "SBC"
    if "obc" in c:
        return "OBC"
    if "sebc" in c or "ebc" in c or "open" in c:
        return "EBC / Open"
    if any(w in c for w in ["minority", "buddha", "christian", "jain", "sikh", "parsi", "jew"]):
        return "Minority"
    if "pwd" in c:
        return "PWD"
    return "All"

def infer_dept(name, desc, state):
    text = (str(name) + " " + str(desc)).lower()
    if "tribal" in text:
        return "Tribal Development Department"
    if any(w in text for w in ["social justice", "special assistance", "sc student"]):
        return "Social Justice & Special Assistance Department"
    if any(w in text for w in ["vjnt", "obc", "sbc"]):
        return "VJNT, OBC & SBC Welfare Department"
    if "medical" in text:
        return "Directorate of Medical Education & Research"
    if any(w in text for w in ["technical", "dte", "panjabrao", "engineering"]):
        return "Directorate of Technical Education (DTE)"
    if "higher education" in text or "dhe" in text:
        return "Directorate of Higher Education (DHE)"
    if "minority" in text:
        return "Minority Development Department"
    if "disabilit" in text or "empowerment of persons" in text:
        return "Department of Empowerment of Persons with Disabilities"
    if state == "Maharashtra":
        return "Government of Maharashtra (MahaDBT)"
    return "Government of India (NSP)"

def infer_benefit(name, desc, qual):
    text = (str(name) + " " + str(desc)).lower()
    if any(w in text for w in ["100%", "full tuition", "freeship"]):
        return "100% Tuition Fee Waiver + Exam Fee"
    if any(w in text for w in ["50%", "half", "shikshan shulkh"]):
        return "50% Tuition Fee Waiver + Exam Fee"
    if any(w in text for w in ["hostel", "vastigruh", "vasatigruh"]):
        return "Hostel Maintenance Allowance (₹20,000 - ₹30,000/yr)"
    if "maintenance allowance" in text:
        return "Maintenance Allowance + Compulsory Fees"
    if "50,000" in text:
        return "₹50,000 per year financial aid"
    if "1,00,000" in text or "1 lakh" in text:
        return "Up to ₹1,00,000 per year"
    m = re.search(r"inr\s*([\d,]+)", text)
    if m:
        return f"Financial aid of INR {m.group(1)}"
    return "Tuition & Academic Allowance"

def infer_est_amount(name, desc, benefit):
    b = (str(name) + " " + str(desc) + " " + str(benefit)).lower()
    if "50,000" in b: return 50000
    if "30,000" in b: return 30000
    if "25,000" in b: return 25000
    if "1,00,000" in b or "1 lakh" in b: return 100000
    if "72,000" in b: return 72000
    if "54,000" in b: return 54000
    if "12,000" in b or "12000" in b: return 12000
    if "10,000" in b: return 10000
    if "100%" in b or "full" in b or "freeship" in b: return 85000
    if "50%" in b or "shikshan shulkh" in b: return 42500
    return 25000

def infer_docs(cat, name):
    c = cat.upper()
    docs = ["CAP Allotment Letter / Admission Receipt", "Income Certificate (Tahsildar issued)", "Domicile Certificate of Maharashtra", "Aadhaar Card Linked to Bank Account", "Previous Year Marksheet"]
    if "SC" in c or "ST" in c:
        docs.extend(["Caste Certificate", "Caste Validity Certificate"])
    elif "OBC" in c or "VJNT" in c or "SBC" in c:
        docs.extend(["Caste Certificate", "Caste Validity Certificate", "Non-Creamy Layer Certificate (NCL)"])
    elif "EBC" in c or "EWS" in c or "OPEN" in c:
        docs.append("EWS / EBC Eligibility Certificate")
    elif "PWD" in c:
        docs.append("Disability Certificate (min. 40%)")
    elif "MINORITY" in c:
        docs.append("Minority Community Declaration / Self-Affidavit")
    return "; ".join(docs)

def main():
    records = []
    scheme_id = 1

    if os.path.exists(RAW_STEP_FILE):
        raw = pd.read_csv(RAW_STEP_FILE, skiprows=8)
        for _, row in raw.iterrows():
            name = str(row["Name"]).strip()
            if not name or name == "nan":
                continue
            state = str(row["State"]).strip()
            state_or_central = "Maharashtra (MahaDBT)" if state == "Maharashtra" else "Central (NSP)"
            cat_raw = str(row["Category"])
            caste_cat = clean_cat(cat_raw)
            try:
                inc = float(row["Income "]) if pd.notna(row["Income "]) else 0
            except:
                inc = 0
            qual = str(row["Qualification"]).strip()
            deg = "B.E./B.Tech, M.Tech, Professional" if any(w in qual.lower() for w in ["professional", "engineer", "tech", "graduat"]) else "Post-Matric / All Levels"
            desc = str(row["Description"]).strip()
            links = str(row["LINKS"]).strip()
            stype = str(row.get("Type ", "Government")).strip()
            dept = infer_dept(name, desc, state)
            benefit = infer_benefit(name, desc, qual)
            est_amt = infer_est_amount(name, desc, benefit)
            docs = infer_docs(caste_cat, name)

            records.append({
                "id": scheme_id,
                "scheme_name": name,
                "state_or_central": state_or_central,
                "department": dept,
                "caste_category": caste_cat,
                "degree_level": deg,
                "max_income_inr": int(inc),
                "benefit_summary": benefit,
                "estimated_annual_benefit_inr": est_amt,
                "eligibility_criteria": f"For {caste_cat} category students. Income limit: Up to ₹{int(inc):,} per year." if inc > 0 else f"For {caste_cat} category students based on academic merit.",
                "required_documents": docs,
                "official_portal_url": links,
                "type": stype,
                "description": desc
            })
            scheme_id += 1

    # High-Priority Flagship Engineering Schemes
    extra_schemes = [
        {
            "scheme_name": "AICTE Pragati Scholarship for Girls (Technical Degree)",
            "state_or_central": "Central (AICTE / NSP)",
            "department": "All India Council for Technical Education (AICTE)",
            "caste_category": "All",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 800000,
            "benefit_summary": "₹50,000 per year towards college fees, laptop/computer, books, and software for all 4 years of B.E.",
            "estimated_annual_benefit_inr": 50000,
            "eligibility_criteria": "Girl students admitted to 1st year B.E./B.Tech at AICTE approved government/autonomous colleges (like GCOEK). Maximum 2 girls per family. Family income <= ₹8 Lakh/annum.",
            "required_documents": "10th & 12th Marksheet; CAP Allotment Letter; Annual Family Income Certificate (< ₹8L); Aadhaar Card; College Bonafide Certificate; Bank Passbook",
            "official_portal_url": "https://scholarships.gov.in/",
            "type": "Government",
            "description": "AICTE Pragati scheme aims to empower young women pursuing technical engineering education by providing ₹50,000 every year of their 4-year undergraduate B.E. course."
        },
        {
            "scheme_name": "AICTE Saksham Scholarship Scheme for Specially-Abled Students (Degree)",
            "state_or_central": "Central (AICTE / NSP)",
            "department": "All India Council for Technical Education (AICTE)",
            "caste_category": "PWD",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 800000,
            "benefit_summary": "₹50,000 per year towards tuition fees, assistive devices, books, and software for all years of B.E.",
            "estimated_annual_benefit_inr": 50000,
            "eligibility_criteria": "Specially-abled students having disability >= 40% admitted to 1st year B.E./B.Tech at AICTE approved colleges. Family income <= ₹8 Lakh/annum.",
            "required_documents": "Disability Certificate issued by Competent Medical Authority (min 40%); Income Certificate (< ₹8L); CAP Allotment Letter; Aadhaar Card; Bank Passbook",
            "official_portal_url": "https://scholarships.gov.in/",
            "type": "Government",
            "description": "AICTE Saksham scheme encourages specially-abled students to pursue technical degrees by assisting with educational expenses and assistive tools."
        },
        {
            "scheme_name": "Dr. Babasaheb Ambedkar Swadhar Yojna",
            "state_or_central": "Maharashtra (MahaDBT)",
            "department": "Social Justice & Special Assistance Department",
            "caste_category": "SC",
            "degree_level": "B.E./B.Tech, M.Tech, Professional",
            "max_income_inr": 250000,
            "benefit_summary": "₹51,000 to ₹60,000 per year for hostel accommodation, food/mess, and book allowances for SC students studying in Kolhapur / Maharashtra",
            "estimated_annual_benefit_inr": 55000,
            "eligibility_criteria": "SC and Navbouddha students who applied for government hostels but could not get admission due to merit or seats, pursuing professional degree in municipal corporation/district cities.",
            "required_documents": "Caste Certificate; Caste Validity Certificate; Income Certificate (< ₹2.5 LPA); College Admission Receipt; Hostel/Mess Rent Agreement / Proof; Bank Account Details",
            "official_portal_url": "https://sjsa.maharashtra.gov.in/",
            "type": "Government",
            "description": "Dr. Babasaheb Ambedkar Swadhar Yojna provides financial assistance to SC students for food, lodging, and books when staying in private accommodations outside government hostels."
        },
        {
            "scheme_name": "Pandit Deendayal Upadhyay Swayam Yojna",
            "state_or_central": "Maharashtra (MahaDBT)",
            "department": "Tribal Development Department",
            "caste_category": "ST",
            "degree_level": "B.E./B.Tech, M.Tech, Professional",
            "max_income_inr": 250000,
            "benefit_summary": "₹51,000 to ₹60,000 per year for hostel, food, and academic expenses for ST students residing in Kolhapur/divisional cities",
            "estimated_annual_benefit_inr": 55000,
            "eligibility_criteria": "Scheduled Tribe (ST) students taking admission in professional colleges who could not secure admission in Government Tribal Hostels.",
            "required_documents": "Tribe Certificate; Tribe Validity Certificate; Income Certificate (< ₹2.5 LPA); College Fee Receipt; Private Residence/Hostel Certificate; Aadhaar Card",
            "official_portal_url": "https://tribal.maharashtra.gov.in/",
            "type": "Government",
            "description": "Swayam Yojna provides direct benefit transfer to ST students pursuing engineering and higher education to cover boarding, lodging, and academic necessities."
        },
        {
            "scheme_name": "Siemens Scholarship Program for Engineering Students",
            "state_or_central": "National Corporate/PSU",
            "department": "Siemens India CSR Foundation",
            "caste_category": "All",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 200000,
            "benefit_summary": "100% Tuition Fee Reimbursement + Allowances for Books, Stationery & Hostel + Free Laptop + Holistic Training",
            "estimated_annual_benefit_inr": 85000,
            "eligibility_criteria": "1st year students of Government Engineering Colleges (like GCOEK) pursuing Mechanical, Electrical, Computer Science, IT, or Electronics. Family income <= ₹2 Lakhs/year. Age max 20 years.",
            "required_documents": "10th & 12th Marksheets; Admission Letter from Government College; Income Certificate (< ₹2 Lakh); Aadhaar Card; Bank Details",
            "official_portal_url": "https://www.siemens.co.in/en/home/company/sustainability/corporate-citizenship/siemens-scholarship-program.html",
            "type": "Private",
            "description": "Prestigious flagship corporate scholarship providing 100% financial and technical mentorship to underprivileged students of Government Engineering Colleges throughout their 4-year degree."
        },
        {
            "scheme_name": "Foundation For Excellence (FFE) Engineering Scholarship",
            "state_or_central": "National Corporate/PSU",
            "department": "Foundation For Excellence India Trust",
            "caste_category": "All",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 300000,
            "benefit_summary": "₹50,000 per year for tuition fees + Free Laptop + Skills and English Mentorship",
            "estimated_annual_benefit_inr": 50000,
            "eligibility_criteria": "1st year B.E./B.Tech students at government or reputed engineering colleges with high MH-CET/JEE Main ranks. Gross family income <= ₹3 Lakh/annum.",
            "required_documents": "CET/JEE Rank Card; 10th & 12th Marksheet; Income Certificate; College Fee Receipt; Electricity Bill / Ration Card",
            "official_portal_url": "https://ffe.org/scholarships/",
            "type": "Private",
            "description": "Nationwide scholarship supporting academically gifted but financially constrained engineering students with annual tuition support, mentorship, and laptops."
        },
        {
            "scheme_name": "Cummins Scholarship Program for Engineering Students",
            "state_or_central": "National Corporate/PSU",
            "department": "Cummins India Foundation",
            "caste_category": "All",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 300000,
            "benefit_summary": "100% Tuition Fees + Exam Fees + Bus/Commute Allowance + Stationery Support",
            "estimated_annual_benefit_inr": 75000,
            "eligibility_criteria": "Engineering degree students from Maharashtra (Pune, Kolhapur, Karad, Satara, etc.) with min 60% in 12th/Diploma. Family income <= ₹3 Lakhs/year.",
            "required_documents": "12th/Diploma Marksheet; Government College Allotment Letter; Income Proof; Address Proof; Bank Account Copy",
            "official_portal_url": "https://www.cummins.com/en/in/company/corporate-responsibility/cummins-india-foundation",
            "type": "Private",
            "description": "Cummins India Foundation provides complete financial assistance to talented students from lower-income backgrounds pursuing B.E. degrees."
        },
        {
            "scheme_name": "ONGC Scholarship for SC/ST Engineering Students",
            "state_or_central": "National Corporate/PSU",
            "department": "Oil and Natural Gas Corporation (ONGC Foundation)",
            "caste_category": "SC",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 450000,
            "benefit_summary": "₹48,000 per year (₹4,000/month) throughout 4 years of engineering studies",
            "estimated_annual_benefit_inr": 48000,
            "eligibility_criteria": "SC/ST students enrolled in 1st year of B.E./B.Tech (Computer, Mechanical, Civil, Electrical, etc.) with min 60% in Class 12. Gross family income <= ₹4.50 Lakhs/annum.",
            "required_documents": "Caste Certificate; Income Certificate; Class 12 Marksheet; College Bonafide Certificate; ECS Form & Bank Passbook",
            "official_portal_url": "https://ongcscholar.org/",
            "type": "Corporate / PSU",
            "description": "ONGC Foundation offers 1,000 scholarships annually to underprivileged SC/ST students enrolled in engineering degree courses across India."
        },
        {
            "scheme_name": "ONGC Scholarship for OBC and General EWS Students",
            "state_or_central": "National Corporate/PSU",
            "department": "Oil and Natural Gas Corporation (ONGC Foundation)",
            "caste_category": "OBC",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 200000,
            "benefit_summary": "₹48,000 per year (₹4,000/month) for 4 years of undergraduate engineering degree",
            "estimated_annual_benefit_inr": 48000,
            "eligibility_criteria": "OBC and General Economically Weaker Section (EWS) 1st year engineering degree students with min 60% in 12th. Gross family income <= ₹2.00 Lakhs/annum.",
            "required_documents": "OBC / EWS Certificate; Income Certificate (< ₹2L); College Identity Card / Bonafide; Bank Account Copy",
            "official_portal_url": "https://ongcscholar.org/",
            "type": "Corporate / PSU",
            "description": "Provides financial support of ₹48,000 per year to meritorious students belonging to OBC and economically weaker general categories studying engineering."
        },
        {
            "scheme_name": "Reliance Foundation Undergraduate Scholarship",
            "state_or_central": "National Corporate/PSU",
            "department": "Reliance Foundation",
            "caste_category": "All",
            "degree_level": "B.E./B.Tech Engineering Degree",
            "max_income_inr": 1500000,
            "benefit_summary": "Up to ₹2,00,000 grant over the course of the undergraduate degree duration",
            "estimated_annual_benefit_inr": 50000,
            "eligibility_criteria": "1st year undergraduate students in any stream (Engineering, Science, etc.) with min 60% in 12th. Household income < ₹15 Lakhs (preference to < ₹2.5 Lakhs). Mandatory aptitude test.",
            "required_documents": "10th & 12th Board Marksheet; Official College Bonafide; Household Income Proof; Aptitude Test Score Card",
            "official_portal_url": "https://www.scholarships.reliancefoundation.org/",
            "type": "Private",
            "description": "5,000 undergraduate scholarships awarded annually to help Indian students pursue higher education with financial security and professional development modules."
        }
    ]

    for s in extra_schemes:
        records.append({
            "id": scheme_id,
            "scheme_name": s["scheme_name"],
            "state_or_central": s["state_or_central"],
            "department": s["department"],
            "caste_category": s["caste_category"],
            "degree_level": s["degree_level"],
            "max_income_inr": s["max_income_inr"],
            "benefit_summary": s["benefit_summary"],
            "estimated_annual_benefit_inr": s["estimated_annual_benefit_inr"],
            "eligibility_criteria": s["eligibility_criteria"],
            "required_documents": s["required_documents"],
            "official_portal_url": s["official_portal_url"],
            "type": s["type"],
            "description": s["description"]
        })
        scheme_id += 1

    df_out = pd.DataFrame(records)
    df_out.to_csv("india_caste_scholarships.csv", index=False, encoding="utf-8")
    print(f"Generated india_caste_scholarships.csv with {len(df_out)} schemes.")

if __name__ == "__main__":
    main()
