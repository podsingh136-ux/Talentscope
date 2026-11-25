
import pandas as pd
import re
import os

# Load cleaned dataset
df = pd.read_csv("data/processed/jobs_cleaned.csv")

os.makedirs("data/processed/analytics", exist_ok=True)

print("Starting TalentScope Job Market Analytics...")


# 1. State-wise job demand
state_data = df[
    ~df["State"].str.lower().isin(["remote", "unknown", ""])
]

state_demand = (
    state_data["State"]
    .value_counts()
    .reset_index()
)

state_demand.columns = ["State", "Job_Postings"]

state_demand.to_csv(
    "data/processed/analytics/state_demand.csv",
    index=False
)


# 2. Most common job titles
top_jobs = (
    df["Job Title"]
    .value_counts()
    .head(15)
    .reset_index()
)

top_jobs.columns = ["Job_Title", "Job_Postings"]

top_jobs.to_csv(
    "data/processed/analytics/top_job_titles.csv",
    index=False
)


# 3. State-wise average monthly salary
salary_data = df.dropna(subset=["salary_avg_monthly"])

salary_data = salary_data[
    ~salary_data["State"].str.lower().isin(["remote", "unknown", ""])
]

salary_by_state = (
    salary_data.groupby("State")
    .agg(
        Average_Monthly_Salary=("salary_avg_monthly", "mean"),
        Salary_Records=("salary_avg_monthly", "count")
    )
    .reset_index()
    .sort_values("Average_Monthly_Salary", ascending=False)
)

salary_by_state.to_csv(
    "data/processed/analytics/salary_by_state.csv",
    index=False
)


# 4. Skill mentions in job titles
# Note: These are title-based mentions, not full job-description skills.

skills = {
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

skill_results = []

for skill, keywords in skills.items():

    count = 0

    for title in df["Job Title"].fillna("").astype(str):
        title = title.lower()

        if any(
            re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", title)
            for word in keywords
        ):
            count += 1

    skill_results.append({
        "Skill": skill,
        "Job_Postings": count
    })


skill_demand = pd.DataFrame(skill_results)

skill_demand = skill_demand.sort_values(
    "Job_Postings",
    ascending=False
)

skill_demand.to_csv(
    "data/processed/analytics/skill_demand.csv",
    index=False
)


# Print analytics report
print("\n========== TALENTSCOPE ANALYTICS REPORT ==========")

print("\n1. Top 10 States:")
print(state_demand.head(10).to_string(index=False))

print("\n2. Top 10 Job Titles:")
print(top_jobs.head(10).to_string(index=False))

print("\n3. Top 10 Skills Mentioned in Job Titles:")
print(skill_demand.head(10).to_string(index=False))

print("\n4. Top 10 States by Average Monthly Salary:")
print(salary_by_state.head(10).round(2).to_string(index=False))

print("\nAnalytics files saved successfully!")
print("Location: data/processed/analytics/")
