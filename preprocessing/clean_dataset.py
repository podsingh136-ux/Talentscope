
import pandas as pd
import re
import os


# Load original dataset
input_file = "data/raw/job_market_india.csv"

df = pd.read_csv(input_file, encoding="utf-8")

print("Starting TalentScope Data Cleaning...")


# Clean text columns
text_columns = ["Job Title", "Location", "Salary", "Locality", "State"]

for col in text_columns:
    df[col] = df[col].fillna("").astype(str).str.strip()


# Normalize salary into monthly INR
def normalize_salary(salary_text):

    text = salary_text.lower()

    # Identify salary period
    if any(word in text for word in ["year", "yearly", "annual", "annum"]):
        divisor = 12

    elif any(word in text for word in ["month", "monthly"]):
        divisor = 1

    else:
        return pd.Series([None, None, None])

    # Extract salary numbers
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?", text)

    if not numbers:
        return pd.Series([None, None, None])

    values = [float(n.replace(",", "")) / divisor for n in numbers]

    minimum = min(values)
    maximum = max(values)
    average = (minimum + maximum) / 2

    return pd.Series([minimum, maximum, average])


df[[
    "salary_min_monthly",
    "salary_max_monthly",
    "salary_avg_monthly"
]] = df["Salary"].apply(normalize_salary)


# Handle missing locality
df["Locality"] = df["Locality"].replace("", "Unknown")


# Remove duplicate records
before = len(df)
df = df.drop_duplicates()
duplicates_removed = before - len(df)


# Create processed folder if it doesn't exist
os.makedirs("data/processed", exist_ok=True)


# Save cleaned dataset
output_file = "data/processed/jobs_cleaned.csv"

df.to_csv(output_file, index=False)


# Display cleaning report
print("\n========== TALENTSCOPE CLEANING REPORT ==========")

print("Original records:", before)
print("Duplicate records removed:", duplicates_removed)
print("Final records:", len(df))

print("\nMonthly salary information:")
print("Available salary records:", df["salary_avg_monthly"].notna().sum())
print("Missing salary records:", df["salary_avg_monthly"].isna().sum())

print("\nTop 10 states:")
print(df["State"].value_counts().head(10))

print("\nCleaned dataset saved at:", output_file)

print("\nDATA CLEANING COMPLETED SUCCESSFULLY!")
