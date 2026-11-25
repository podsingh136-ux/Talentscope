import os
import json
import re
import joblib
from flask import Flask, render_template, jsonify, request
import pandas as pd
import io
from datetime import datetime
from flask import Response, send_file
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


app = Flask(__name__)

# Load ML model once at startup for faster predictions
MODEL_PATH = "models/saved/job_demand_model.pkl"
demand_model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

SKILL_KEYWORDS = {
    "Python": ["python"],
    "Java": ["java"],
    "HTML": ["html"],
    "CSS": ["css"],
    "JavaScript": ["javascript"],
    "SQL": ["sql"],
    "Excel": ["excel"],
    "Power BI": ["power bi"],
    "Machine Learning": ["machine learning"],
    "Data Analysis": ["data analyst", "data analysis"],
    "Robotics": ["robotics"],
    "Artificial Intelligence": ["artificial intelligence"],
    "Teaching": ["teacher", "teaching", "trainer"]
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "TalentScope backend is running!"
    })


@app.route("/api/dashboard")
def dashboard():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        skills = pd.read_csv(
            "data/processed/analytics/skill_demand.csv"
        )

        total_jobs = len(jobs)
        total_roles = jobs["Job Title"].nunique()
        total_locations = jobs["Location"].nunique()

        skills_tracked = int(
            (skills["Job_Postings"] > 0).sum()
        )

        top_skills = skills.sort_values(
            "Job_Postings",
            ascending=False
        ).head(5)

        role_counts = jobs["Job Title"].value_counts()
        top_roles = role_counts.head(4)
        other_jobs = int(role_counts.iloc[4:].sum())

        role_labels = top_roles.index.tolist()
        role_values = [int(x) for x in top_roles.values]

        if other_jobs > 0:
            role_labels.append("Other")
            role_values.append(other_jobs)

        return jsonify({
            "total_jobs": int(total_jobs),
            "total_roles": int(total_roles),
            "total_locations": int(total_locations),
            "skills_tracked": skills_tracked,

            "skills": {
                "labels": top_skills["Skill"].tolist(),
                "values": [
                    int(x) for x in top_skills["Job_Postings"]
                ]
            },

            "roles": {
                "labels": role_labels,
                "values": role_values
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/insights")
def insights():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")

        skills = pd.read_csv(
            "data/processed/analytics/skill_demand.csv"
        )

        top_skills = skills.sort_values(
            "Job_Postings",
            ascending=False
        ).head(10)

        state_jobs = jobs[
            ~jobs["State"].str.lower().isin(
                ["remote", "unknown", ""]
            )
        ]

        state_demand = (
            state_jobs["State"]
            .value_counts()
            .head(10)
        )

        salary_data = state_jobs.dropna(
            subset=["salary_avg_monthly"]
        )

        salary_data = salary_data[
            salary_data["salary_avg_monthly"] > 0
        ]

        salary_analysis = (
            salary_data.groupby("State")
            .agg(
                average_salary=("salary_avg_monthly", "mean"),
                salary_records=("salary_avg_monthly", "count")
            )
            .reset_index()
            .sort_values(
                "average_salary",
                ascending=False
            )
            .head(10)
        )

        return jsonify({
            "top_skills": {
                "labels": top_skills["Skill"].tolist(),
                "values": [
                    int(x) for x in top_skills["Job_Postings"]
                ]
            },

            "state_demand": {
                "labels": state_demand.index.tolist(),
                "values": [
                    int(x) for x in state_demand.values
                ]
            },

            "salary_analysis": {
                "labels": salary_analysis["State"].tolist(),
                "values": [
                    round(float(x), 2)
                    for x in salary_analysis["average_salary"]
                ],
                "records": [
                    int(x) for x in salary_analysis["salary_records"]
                ]
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/trends")
def employment_trends():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")

        # 1. Work Mode Trend (Remote vs On-site)
        is_remote = jobs["State"].str.strip().str.lower() == "remote"
        remote_count = int(is_remote.sum())
        onsite_count = int((~is_remote).sum())

        # 2. Salary Bracket Distribution (for valid salaries)
        valid_salaries = jobs["salary_avg_monthly"].dropna()
        valid_salaries = valid_salaries[valid_salaries > 0]

        below_15k = int((valid_salaries < 15000).sum())
        between_15k_25k = int(((valid_salaries >= 15000) & (valid_salaries < 25000)).sum())
        between_25k_40k = int(((valid_salaries >= 25000) & (valid_salaries < 40000)).sum())
        above_40k = int((valid_salaries >= 40000).sum())

        # 3. Role Level / Hiring Category Trend (from Job Title keywords)
        titles_lower = jobs["Job Title"].fillna("").str.lower()

        fresher_mask = titles_lower.str.contains(
            r"\b(?:fresher|freshers|trainee|intern|internship|graduate|entry)\b",
            regex=True
        )
        senior_mask = titles_lower.str.contains(
            r"\b(?:manager|lead|senior|head|supervisor|specialist|consultant|director)\b",
            regex=True
        ) & (~fresher_mask)

        fresher_count = int(fresher_mask.sum())
        senior_count = int(senior_mask.sum())
        general_count = int(len(jobs) - fresher_count - senior_count)

        return jsonify({
            "status": "success",
            "note": "Trends are derived from job attributes; dataset does not contain posting dates.",
            "work_mode": {
                "labels": ["On-site", "Remote"],
                "values": [onsite_count, remote_count]
            },
            "salary_brackets": {
                "labels": ["Below ₹15k", "₹15k - ₹25k", "₹25k - ₹40k", "Above ₹40k"],
                "values": [below_15k, between_15k_25k, between_25k_40k, above_40k]
            },
            "role_levels": {
                "labels": ["Fresher / Trainee / Intern", "General / Executive Roles", "Manager / Lead / Specialist"],
                "values": [fresher_count, general_count, senior_count]
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/filter-options")
def filter_options():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        states = sorted([
            str(s).strip() for s in jobs["State"].dropna().unique().tolist()
            if str(s).strip() != ""
        ])
        skills = sorted(list(SKILL_KEYWORDS.keys()))

        return jsonify({
            "status": "success",
            "states": states,
            "skills": skills
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/filtered-data")
def filtered_data():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")

        selected_state = request.args.get("state", "").strip()
        selected_skill = request.args.get("skill", "").strip()
        role_query = request.args.get("role", "").strip().lower()
        min_salary = request.args.get("min_salary", "").strip()

        df = jobs.copy()

        # 1. State Filter
        if selected_state:
            df = df[df["State"].str.strip().str.lower() == selected_state.lower()]

        # 2. Skill Filter (keyword match in Job Title)
        if selected_skill and selected_skill in SKILL_KEYWORDS:
            keywords = SKILL_KEYWORDS[selected_skill]
            pattern = "|".join(
                r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords
            )
            df = df[df["Job Title"].fillna("").str.lower().str.contains(pattern, regex=True)]

        # 3. Job Role Keyword Filter
        if role_query:
            df = df[df["Job Title"].fillna("").str.lower().str.contains(re.escape(role_query), regex=True)]

        # 4. Minimum Monthly Salary Filter
        if min_salary:
            try:
                min_sal_val = float(min_salary)
                df = df[df["salary_avg_monthly"].notna() & (df["salary_avg_monthly"] >= min_sal_val)]
            except ValueError:
                pass

        # --- KPIs ---
        total_jobs = int(len(df))
        total_roles = int(df["Job Title"].nunique())
        total_locations = int(df["Location"].nunique())

        # --- Skill Counts on Filtered Data ---
        skill_counts = []
        titles_series = df["Job Title"].fillna("").astype(str).str.lower()
        for skill, keywords in SKILL_KEYWORDS.items():
            pattern = "|".join(
                r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords
            )
            cnt = int(titles_series.str.contains(pattern, regex=True).sum())
            if cnt > 0:
                skill_counts.append({"Skill": skill, "Job_Postings": cnt})

        skill_counts.sort(key=lambda x: x["Job_Postings"], reverse=True)
        skills_tracked = len(skill_counts)

        top5_skills = skill_counts[:5]
        top10_skills = skill_counts[:10]

        # --- Role Distribution (Top 4 + Other) ---
        role_counts = df["Job Title"].value_counts()
        top_roles = role_counts.head(4)
        other_jobs = int(role_counts.iloc[4:].sum())
        role_labels = top_roles.index.tolist()
        role_values = [int(x) for x in top_roles.values]
        if other_jobs > 0:
            role_labels.append("Other")
            role_values.append(other_jobs)

        # --- State Demand ---
        state_jobs = df[~df["State"].str.lower().isin(["remote", "unknown", ""])]
        state_demand = state_jobs["State"].value_counts().head(10)

        # --- Salary Analysis ---
        salary_data = state_jobs.dropna(subset=["salary_avg_monthly"])
        salary_data = salary_data[salary_data["salary_avg_monthly"] > 0]
        salary_analysis = (
            salary_data.groupby("State")
            .agg(
                average_salary=("salary_avg_monthly", "mean"),
                salary_records=("salary_avg_monthly", "count")
            )
            .reset_index()
            .sort_values("average_salary", ascending=False)
            .head(10)
        )

        # --- Trends ---
        is_remote = df["State"].str.strip().str.lower() == "remote"
        remote_count = int(is_remote.sum())
        onsite_count = int((~is_remote).sum())

        valid_sal = df["salary_avg_monthly"].dropna()
        valid_sal = valid_sal[valid_sal > 0]
        below_15k = int((valid_sal < 15000).sum())
        b_15_25 = int(((valid_sal >= 15000) & (valid_sal < 25000)).sum())
        b_25_40 = int(((valid_sal >= 25000) & (valid_sal < 40000)).sum())
        above_40k = int((valid_sal >= 40000).sum())

        fresher_mask = titles_series.str.contains(
            r"\b(?:fresher|freshers|trainee|intern|internship|graduate|entry)\b",
            regex=True
        )
        senior_mask = titles_series.str.contains(
            r"\b(?:manager|lead|senior|head|supervisor|specialist|consultant|director)\b",
            regex=True
        ) & (~fresher_mask)
        fresher_count = int(fresher_mask.sum())
        senior_count = int(senior_mask.sum())
        general_count = int(len(df) - fresher_count - senior_count)

        return jsonify({
            "status": "success",
            "total_jobs": total_jobs,
            "total_roles": total_roles,
            "total_locations": total_locations,
            "skills_tracked": skills_tracked,
            "skills": {
                "labels": [s["Skill"] for s in top5_skills],
                "values": [s["Job_Postings"] for s in top5_skills]
            },
            "top_skills": {
                "labels": [s["Skill"] for s in top10_skills],
                "values": [s["Job_Postings"] for s in top10_skills]
            },
            "roles": {
                "labels": role_labels,
                "values": role_values
            },
            "state_demand": {
                "labels": state_demand.index.tolist(),
                "values": [int(x) for x in state_demand.values]
            },
            "salary_analysis": {
                "labels": salary_analysis["State"].tolist(),
                "values": [round(float(x), 2) for x in salary_analysis["average_salary"]],
                "records": [int(x) for x in salary_analysis["salary_records"]]
            },
            "work_mode": {
                "labels": ["On-site", "Remote"],
                "values": [onsite_count, remote_count]
            },
            "salary_brackets": {
                "labels": ["Below ₹15k", "₹15k - ₹25k", "₹25k - ₹40k", "Above ₹40k"],
                "values": [below_15k, b_15_25, b_25_40, above_40k]
            },
            "role_levels": {
                "labels": ["Fresher / Trainee / Intern", "General / Executive Roles", "Manager / Lead / Specialist"],
                "values": [fresher_count, general_count, senior_count]
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/advanced-analytics")
def advanced_analytics():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        titles_lower = jobs["Job Title"].fillna("").astype(str).str.lower()

        # 1. Job Domain / Functional Sector Classification (derived from Job Title keywords)
        domain_rules = [
            ("IT & Software", r"\b(?:software|developer|python|java|html|web|data|ai|machine learning|cloud|cyber|qa|tester|mern|php|flutter|it|system|network|database)\b"),
            ("Sales & Marketing", r"\b(?:sales|marketing|business development|bde|bda|telecaller|telecalling|seo|ppc|ads|promoter|lead generation)\b"),
            ("Education & Training", r"\b(?:teacher|teaching|trainer|tutor|faculty|professor|counsellor|counselor|coach|academic|accademic)\b"),
            ("Operations & Logistics", r"\b(?:delivery|operations|warehouse|logistics|driver|helper|packer|supervisor|incharge|admin|office|receptionist|back office)\b"),
            ("Finance & Accounts", r"\b(?:accountant|accounts|finance|financial|billing|audit|ca|cma|icwa|bank|banking|tax)\b"),
            ("Design & Media", r"\b(?:designer|design|video|editor|editing|content|writer|photographer|photography|3d|ui|ux|graphic)\b"),
            ("Healthcare & Pharma", r"\b(?:nurse|doctor|medical|physiotherapist|surgeon|chemist|pharmacy|healthcare|drug)\b")
        ]

        domain_counts = {}
        assigned = pd.Series(False, index=jobs.index)

        for domain_name, pattern in domain_rules:
            mask = titles_lower.str.contains(pattern, regex=True) & (~assigned)
            domain_counts[domain_name] = int(mask.sum())
            assigned = assigned | mask

        domain_counts["General & Trainees"] = int((~assigned).sum())
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)

        # 2. Skill-wise Average Monthly Salary (for skills with valid salary records)
        skill_salary_list = []
        for skill, keywords in SKILL_KEYWORDS.items():
            pattern = "|".join(r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords)
            matched = jobs[titles_lower.str.contains(pattern, regex=True)]
            valid_sal = matched["salary_avg_monthly"].dropna()
            valid_sal = valid_sal[valid_sal > 0]
            if len(valid_sal) > 0:
                skill_salary_list.append({
                    "skill": skill,
                    "avg_salary": round(float(valid_sal.mean()), 2),
                    "postings": int(len(matched)),
                    "salary_records": int(len(valid_sal))
                })

        skill_salary_list.sort(key=lambda x: x["avg_salary"], reverse=True)

        # 3. Remote vs On-site Salary & Overall Median vs Mean Comparison
        valid_all = jobs[jobs["salary_avg_monthly"].notna() & (jobs["salary_avg_monthly"] > 0)]
        overall_mean = round(float(valid_all["salary_avg_monthly"].mean()), 2) if len(valid_all) else 0
        overall_median = round(float(valid_all["salary_avg_monthly"].median()), 2) if len(valid_all) else 0

        remote_sal = valid_all[valid_all["State"].str.strip().str.lower() == "remote"]["salary_avg_monthly"]
        onsite_sal = valid_all[valid_all["State"].str.strip().str.lower() != "remote"]["salary_avg_monthly"]

        remote_avg = round(float(remote_sal.mean()), 2) if len(remote_sal) else 0
        onsite_avg = round(float(onsite_sal.mean()), 2) if len(onsite_sal) else 0

        # 4. Skill Gap Analysis (High-demand skills vs 0-mention skills in titles)
        present_skills = []
        absent_skills = []
        for skill, keywords in SKILL_KEYWORDS.items():
            pattern = "|".join(r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords)
            cnt = int(titles_series := titles_lower.str.contains(pattern, regex=True).sum())
            if cnt > 0:
                present_skills.append({"skill": skill, "count": cnt})
            else:
                absent_skills.append(skill)

        present_skills.sort(key=lambda x: x["count"], reverse=True)

        # 5. Automated Key Analytical Insights
        top_state_row = jobs[~jobs["State"].str.lower().isin(["remote", "unknown", ""])]["State"].value_counts()
        top_state_name = top_state_row.index[0] if len(top_state_row) else "N/A"
        top_state_cnt = int(top_state_row.iloc[0]) if len(top_state_row) else 0

        insights_summary = [
            f"Top Hiring Hub: {top_state_name} leads with {top_state_cnt} job postings across the dataset.",
            f"Salary Skew Insight: Overall average monthly pay is ₹{overall_mean:,.0f}, whereas the median pay is ₹{overall_median:,.0f} (indicating high-paying outliers pull the average up).",
            f"Work Mode Pay Gap: On-site roles average ₹{onsite_avg:,.0f}/month compared to ₹{remote_avg:,.0f}/month for Remote postings.",
            f"Title Keyword Limitation: Only {len(present_skills)} of {len(SKILL_KEYWORDS)} tracked skills appear explicitly in job titles; {', '.join(absent_skills)} have 0 title-only matches because full job descriptions are not in the dataset."
        ]

        return jsonify({
            "status": "success",
            "domain_distribution": {
                "labels": [d[0] for d in sorted_domains],
                "values": [d[1] for d in sorted_domains]
            },
            "skill_salary": {
                "labels": [s["skill"] for s in skill_salary_list],
                "values": [s["avg_salary"] for s in skill_salary_list],
                "records": [s["salary_records"] for s in skill_salary_list]
            },
            "salary_comparison": {
                "overall_mean": overall_mean,
                "overall_median": overall_median,
                "onsite_avg": onsite_avg,
                "remote_avg": remote_avg,
                "disclosed_count": int(len(valid_all)),
                "undisclosed_count": int(len(jobs) - len(valid_all))
            },
            "skill_gap": {
                "present": present_skills,
                "absent": absent_skills
            },
            "key_insights": insights_summary
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/predict-demand", methods=["POST"])
def predict_demand():
    try:
        data = request.get_json() or {}
        job_title = data.get("job_title", "").strip()

        if not job_title:
            return jsonify({
                "status": "error",
                "message": "Please enter a job title"
            }), 400

        model = demand_model if demand_model is not None else joblib.load(MODEL_PATH)

        prediction = model.predict([job_title])[0]
        probabilities = model.predict_proba([job_title])[0]

        confidence = round(
            float(max(probabilities)) * 100,
            2
        )

        return jsonify({
            "status": "success",
            "job_title": job_title,
            "predicted_demand": prediction,
            "confidence": confidence
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route("/api/ml-metrics")
def ml_metrics():
    try:
        metrics_path = "models/saved/model_metrics.json"
        if not os.path.exists(metrics_path):
            return jsonify({
                "status": "error",
                "message": "Metrics file not found. Run train_model.py first."
            }), 404

        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics = json.load(f)

        return jsonify({
            "status": "success",
            "metrics": metrics
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
@app.route("/api/recommend-jobs", methods=["POST"])
def recommend_jobs():
    try:
        data = request.get_json() or {}
        raw_skills = data.get("skills", "").strip()

        if not raw_skills:
            return jsonify({
                "status": "error",
                "message": "Please enter at least one skill (e.g., Python, Data Analysis, HTML)."
            }), 400

        # Parse comma-separated user skills
        user_tokens = [s.strip().lower() for s in raw_skills.split(",") if s.strip()]
        if not user_tokens:
            return jsonify({
                "status": "error",
                "message": "Please provide valid comma-separated skills."
            }), 400

        # Expand tokens using SKILL_KEYWORDS aliases (e.g., 'data analysis' -> ['data analyst', 'data analysis'])
        search_terms = {}
        for token in user_tokens:
            matched_canonical = None
            for canonical, aliases in SKILL_KEYWORDS.items():
                if token == canonical.lower() or token in aliases:
                    matched_canonical = canonical
                    search_terms[canonical] = aliases
                    break
            if not matched_canonical:
                search_terms[token.title()] = [token]

        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        skills_df = pd.read_csv("data/processed/analytics/skill_demand.csv")
        top_demanded_skills = skills_df[skills_df["Job_Postings"] > 0]["Skill"].head(6).tolist()

        recommendations = []
        seen_pairs = set()

        for _, row in jobs.iterrows():
            title = str(row["Job Title"]).strip()
            title_lower = title.lower()
            location = str(row["Location"]).strip()
            state = str(row["State"]).strip()

            # Deduplicate identical title + location pairs
            pair_key = (title_lower, location.lower())
            if pair_key in seen_pairs:
                continue

            matched_skills = []
            for label, aliases in search_terms.items():
                if any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", title_lower) for alias in aliases):
                    matched_skills.append(label)

            if matched_skills:
                seen_pairs.add(pair_key)
                avg_sal = row.get("salary_avg_monthly")
                salary_display = (
                    f"₹{round(float(avg_sal)):,}/month"
                    if pd.notna(avg_sal) and float(avg_sal) > 0
                    else str(row.get("Salary", "Not specified"))
                )

                # Suggest complementary demanded skills from dataset not already matched
                suggested_upskill = [
                    s for s in top_demanded_skills
                    if s.lower() not in [m.lower() for m in matched_skills]
                ][:3]

                reason = (
                    f"Directly matches your skill(s): {', '.join(matched_skills)} "
                    f"in the job title '{title}' ({state})."
                )

                recommendations.append({
                    "job_title": title,
                    "location": location,
                    "state": state,
                    "salary": salary_display,
                    "matched_skills": matched_skills,
                    "match_count": len(matched_skills),
                    "demanded_skills": suggested_upskill,
                    "reason": reason
                })

        # Rank by number of matched skills first
        recommendations.sort(key=lambda x: x["match_count"], reverse=True)
        top_recs = recommendations[:10]

        return jsonify({
            "status": "success",
            "input_skills": list(search_terms.keys()),
            "total_matches": len(recommendations),
            "recommendations": top_recs,
            "top_market_skills": top_demanded_skills,
            "note": "Recommendations are matched strictly against real job titles in jobs_cleaned.csv."
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
def apply_job_filters(df, selected_state="", selected_skill="", role_query="", min_salary=""):
    """Reusable helper to filter jobs dataframe consistently across APIs and exports."""
    filtered = df.copy()
    if selected_state:
        filtered = filtered[filtered["State"].str.strip().str.lower() == selected_state.lower()]

    if selected_skill and selected_skill in SKILL_KEYWORDS:
        keywords = SKILL_KEYWORDS[selected_skill]
        pattern = "|".join(r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords)
        filtered = filtered[filtered["Job Title"].fillna("").str.lower().str.contains(pattern, regex=True)]

    if role_query:
        filtered = filtered[filtered["Job Title"].fillna("").str.lower().str.contains(re.escape(role_query.lower()), regex=True)]

    if min_salary:
        try:
            min_sal_val = float(min_salary)
            filtered = filtered[filtered["salary_avg_monthly"].notna() & (filtered["salary_avg_monthly"] >= min_sal_val)]
        except ValueError:
            pass

    return filtered


@app.route("/api/export/csv")
def export_csv():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        selected_state = request.args.get("state", "").strip()
        selected_skill = request.args.get("skill", "").strip()
        role_query = request.args.get("role", "").strip()
        min_salary = request.args.get("min_salary", "").strip()

        filtered = apply_job_filters(jobs, selected_state, selected_skill, role_query, min_salary)

        csv_buffer = io.StringIO()
        filtered.to_csv(csv_buffer, index=False)
        csv_bytes = io.BytesIO(csv_buffer.getvalue().encode("utf-8-sig"))

        return send_file(
            csv_bytes,
            mimetype="text/csv",
            as_attachment=True,
            download_name="TalentScope_Job_Market_Data.csv"
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/export/pdf")
def export_pdf():
    try:
        jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
        selected_state = request.args.get("state", "").strip()
        selected_skill = request.args.get("skill", "").strip()
        role_query = request.args.get("role", "").strip()
        min_salary = request.args.get("min_salary", "").strip()

        df = apply_job_filters(jobs, selected_state, selected_skill, role_query, min_salary)

        total_jobs = len(df)
        total_roles = df["Job Title"].nunique()
        total_locations = df["Location"].nunique()
        remote_jobs = int((df["State"].str.strip().str.lower() == "remote").sum())

        valid_sal = df["salary_avg_monthly"].dropna()
        valid_sal = valid_sal[valid_sal > 0]
        mean_sal = f"INR {valid_sal.mean():,.2f}" if len(valid_sal) else "N/A"
        median_sal = f"INR {valid_sal.median():,.2f}" if len(valid_sal) else "N/A"

        # Active filter description
        filter_parts = []
        if selected_state:
            filter_parts.append(f"State={selected_state}")
        if selected_skill:
            filter_parts.append(f"Skill={selected_skill}")
        if role_query:
            filter_parts.append(f"Role='{role_query}'")
        if min_salary:
            filter_parts.append(f"MinSalary>=INR {min_salary}")
        filter_desc = ", ".join(filter_parts) if filter_parts else "None (Full Cleaned Dataset - 830 records)"

        # Compute top states & top skills for charts
        state_jobs = df[~df["State"].str.lower().isin(["remote", "unknown", ""])]
        top_states = state_jobs["State"].value_counts().head(8)

        titles_lower = df["Job Title"].fillna("").astype(str).str.lower()
        skill_pairs = []
        for skill, keywords in SKILL_KEYWORDS.items():
            pattern = "|".join(r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in keywords)
            cnt = int(titles_lower.str.contains(pattern, regex=True).sum())
            if cnt > 0:
                skill_pairs.append((skill, cnt))
        skill_pairs.sort(key=lambda x: x[1], reverse=True)
        top_skills = skill_pairs[:8]

        pdf_buffer = io.BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            fig = plt.figure(figsize=(8.27, 11.69))  # A4 Portrait
            fig.patch.set_facecolor("white")

            # Header Banner
            fig.text(0.07, 0.94, "TALENTSCOPE - JOB MARKET INTELLIGENCE REPORT", fontsize=15, fontweight="bold", color="#1e3a8a")
            fig.text(0.07, 0.915, "Analyzing Industry Skill Demand and Employment Trends Using Data Analytics", fontsize=9.5, color="#475569")
            fig.text(0.07, 0.895, f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}  |  Filters: {filter_desc}", fontsize=8.5, color="#64748b")

            # KPI Summary Box
            kpi_text = (
                f"EXECUTIVE SUMMARY (KPIs)\n"
                f"• Total Filtered Job Postings: {total_jobs}    |    Unique Job Roles: {total_roles}    |    Hiring Locations: {total_locations}\n"
                f"• Remote Job Postings: {remote_jobs} ({(remote_jobs/total_jobs*100):.1f}% if total_jobs else 0%)    |    Disclosed Salary Records: {len(valid_sal)}\n"
                f"• Mean Monthly Salary: {mean_sal}    |    Median Monthly Salary: {median_sal}"
                if total_jobs > 0 else
                "EXECUTIVE SUMMARY: No records matched the selected filter criteria."
            )
            fig.text(
                0.07, 0.80, kpi_text, fontsize=9, color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.7", facecolor="#eff6ff", edgecolor="#93c5fd")
            )

            # Chart 1: Top States
            ax1 = fig.add_axes([0.10, 0.50, 0.80, 0.24])
            if len(top_states) > 0:
                ax1.barh(top_states.index[::-1], top_states.values[::-1], color="#3b82f6")
                ax1.set_title("Top Hiring States by Job Postings", fontsize=11, fontweight="bold", color="#1e293b")
                ax1.set_xlabel("Number of Postings", fontsize=9)
                ax1.tick_params(labelsize=8.5)
            else:
                ax1.text(0.5, 0.5, "No state-level records in current filter", ha="center", va="center")
                ax1.axis("off")

            # Chart 2: Top Skills in Titles
            ax2 = fig.add_axes([0.10, 0.21, 0.80, 0.22])
            if len(top_skills) > 0:
                s_labels = [x[0] for x in top_skills][::-1]
                s_vals = [x[1] for x in top_skills][::-1]
                ax2.barh(s_labels, s_vals, color="#8b5cf6")
                ax2.set_title("Top Skill Mentions in Job Titles", fontsize=11, fontweight="bold", color="#1e293b")
                ax2.set_xlabel("Job Title Mentions", fontsize=9)
                ax2.tick_params(labelsize=8.5)
            else:
                ax2.text(0.5, 0.5, "No tracked skill keyword matches in current filter", ha="center", va="center")
                ax2.axis("off")

            # Methodology & Dataset Limitations Footer
            lim_text = (
                "KEY FINDINGS & DATASET LIMITATIONS:\n"
                "1. Skill counts reflect explicit keyword matches in Job Titles (full job descriptions are not present in the raw CSV).\n"
                "2. Monthly salaries are normalized from annual/monthly text strings; undisclosed salaries are excluded from averages.\n"
                "3. Demand predictions use TF-IDF (1-2 n-grams) + Balanced Logistic Regression trained on dataset role frequencies."
            )
            fig.text(
                0.07, 0.06, lim_text, fontsize=8, color="#78350f",
                bbox=dict(boxstyle="round,pad=0.6", facecolor="#fffbeb", edgecolor="#fcd34d")
            )

            pdf.savefig(fig)
            plt.close(fig)

        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="TalentScope_Analytics_Report.pdf"
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
