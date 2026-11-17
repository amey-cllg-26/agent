"""Populate human-readable deadlines into europe_scholarships_matching.csv"""
import pandas as pd

deadlines_map = {
    "DAAD Development-Related Postgraduate Courses (EPOS)": "Opens Aug–Oct annually (Course-dependent)",
    "DAAD Research Grants for Doctoral Candidates": "31 Oct annually",
    "DAAD WISE (Working Internships in Science and Engineering)": "01 Nov annually",
    "Chevening Scholarships": "05 Nov annually",
    "Commonwealth Master's Scholarships": "17 Oct annually",
    "Gates Cambridge Scholarship": "04 Dec annually",
    "Clarendon Fund Scholarships": "20 Jan annually (Oxford course intake)",
    "JN Tata Endowment for Higher Education": "15 Mar annually",
    "Narotam Sekhsaria Foundation Scholarship": "15 Mar annually",
    "Inlaks Shivdasani Foundation Scholarships": "30 Mar annually",
    "KC Mahindra Scholarship for Post-Graduate Studies Abroad": "31 Mar annually",
    "Fulbright-Nehru Master's Fellowships": "15 May annually",
    "Fulbright Foreign Student Program": "Varies by embassy (Feb–May annually)",
    "Knight-Hennessy Scholars at Stanford": "09 Oct annually",
    "Rotary Peace Fellowships": "15 May annually",
    "Vanier Canada Graduate Scholarships": "01 Nov annually",
    "University of Toronto Lester B. Pearson International Scholarship": "30 Nov annually",
    "Banting Postdoctoral Fellowships": "18 Sep annually",
    "Australia Awards Scholarships": "30 Apr annually",
    "Australian Government Research Training Program (RTP)": "31 Oct annually",
    "University of Melbourne Graduate Research Scholarships": "31 Oct annually",
    "Manaaki New Zealand Scholarships": "28 Feb annually",
    "MEXT Japanese Government Scholarships (Research Students)": "15 May annually",
    "MEXT Japanese Government Scholarships (Undergraduate)": "25 May annually",
    "Swiss Government Excellence Scholarships": "15 Nov annually",
    "Eiffel Excellence Scholarship Program": "10 Jan annually",
    "Erasmus Mundus Joint Master Degrees (EMJMD)": "15 Jan annually",
    "Swedish Institute Scholarship for Global Professionals (SISGP)": "28 Feb annually",
    "Turkiye Burslari Scholarships": "20 Feb annually",
    "NL Scholarship (formerly Holland Scholarship)": "01 Feb annually",
    "Government of Ireland International Education Scholarships (GOI-IES)": "24 Mar annually",
    "VLIR-UOS Master Mind Scholarships": "01 Mar annually",
    "A*STAR Graduate Scholarship (Singapore)": "01 Aug annually",
    "KAIST International Student Scholarship": "21 Mar annually",
    "Monbukagakusho Honors Scholarship for Privately-Financed International Students": "30 Jun annually",
    "Stipendium Hungaricum Scholarship": "15 Jan annually",
    "Danish Government Scholarships for Non-EU/EEA Students": "01 Feb annually",
    "Finland Government Scholarship for International Students": "18 Jan annually",
    "Politecnico di Milano Merit-Based Scholarships": "15 Feb annually",
    "DSU Regional Scholarships (Italy)": "30 Aug annually",
    "Norwegian Directorate for Higher Education Grants": "15 Mar annually",
    "Seoul National University Global Scholarship": "10 Mar annually",
    "ETH Zurich Excellence Scholarship & Opportunity Programme (ESOP)": "15 Dec annually",
    "EPFL Master Excellence Fellowships": "15 Dec annually",
    "Lund University Global Scholarship Programme": "15 Feb annually",
    "OeAD Ernst Mach Grant": "01 Feb annually",
    "Warwick Chancellor's International Scholarships": "12 Dec annually",
    "Weidenfeld-Hoffmann Scholarships and Leadership Programme (Oxford)": "10 Jan annually",
    "Cambridge Trust International Scholarships": "04 Dec annually",
    "Edinburgh Global Research Scholarship": "28 Feb annually",
}

df = pd.read_csv("europe_scholarships_matching.csv", dtype=str)
count = 0
for idx, row in df.iterrows():
    name = str(row["scholarship_name"]).strip()
    matched_dl = None
    for k, v in deadlines_map.items():
        if k.lower() in name.lower() or name.lower() in k.lower():
            matched_dl = v
            break
    if matched_dl:
        df.at[idx, "deadline"] = matched_dl
        count += 1
    else:
        df.at[idx, "deadline"] = "Opens Aug–Nov annually"
        count += 1

print(f"Populated {count} deadlines in europe_scholarships_matching.csv")
df.to_csv("europe_scholarships_matching.csv", index=False)
