import os
import re
import json
import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend so PNG saves cleanly without opening a window
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)


def normalize_title(title):
    """Normalize minor punctuation/slash variations so equivalent titles group cleanly."""
    text = str(title).lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Unify swapped slash titles like 'delivery partner delivery executive'
    if text == "delivery executive delivery partner":
        text = "delivery partner delivery executive"
    return text


print("Starting TalentScope Improved ML Training & Evaluation...")

# 1. Load cleaned dataset
jobs = pd.read_csv("data/processed/jobs_cleaned.csv")
jobs = jobs.dropna(subset=["Job Title"]).copy()
jobs["Normalized_Title"] = jobs["Job Title"].apply(normalize_title)

# 2. Compute role frequency on normalized titles
role_counts = jobs["Normalized_Title"].value_counts()


def classify_demand(norm_title):
    count = role_counts.get(norm_title, 0)
    if count >= 5:
        return "High Demand"
    elif count >= 2:
        return "Medium Demand"
    else:
        return "Low Demand"


jobs["Demand"] = jobs["Normalized_Title"].apply(classify_demand)

X = jobs["Normalized_Title"]
y = jobs["Demand"]

print("\nDemand Category Distribution (Post-Normalization):")
print(y.value_counts())

# 3. Stratified Train-Test Split (80% Train, 20% Test)
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 4. Compare Multiple Suitable Text Classification Models
candidate_models = {
    "Logistic Regression (Balanced)": Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ]),
    "Multinomial Naive Bayes": Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("classifier", MultinomialNB())
    ]),
    "Random Forest (Balanced)": Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("classifier", RandomForestClassifier(n_estimators=150, class_weight="balanced", random_state=42))
    ])
}

comparison_results = []
best_model = None
best_preds = None
best_accuracy = 0.0

for name, pipe in candidate_models.items():
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    acc = round(float(accuracy_score(y_test, preds)) * 100, 2)
    report_dict = classification_report(y_test, preds, output_dict=True, zero_division=0)
    macro_f1 = round(float(report_dict["macro avg"]["f1-score"]) * 100, 2)

    comparison_results.append({
        "model": name,
        "accuracy": acc,
        "macro_f1": macro_f1
    })

    print(f"\n--- {name} ---")
    print(f"Accuracy: {acc}% | Macro F1: {macro_f1}%")

    if name == "Logistic Regression (Balanced)":
        best_model = pipe
        best_preds = preds
        best_accuracy = acc

# 5. Detailed Classification Report for Selected Model
class_labels = ["High Demand", "Medium Demand", "Low Demand"]
detailed_report = classification_report(
    y_test,
    best_preds,
    labels=class_labels,
    output_dict=True,
    zero_division=0
)

print("\nSelected Model Classification Report (Logistic Regression):")
print(classification_report(y_test, best_preds, labels=class_labels, zero_division=0))

# 6. Generate and Save Confusion Matrix Plot
os.makedirs("static/images", exist_ok=True)
cm = confusion_matrix(y_test, best_preds, labels=class_labels)

fig, ax = plt.subplots(figsize=(6.5, 5))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_labels)
disp.plot(ax=ax, cmap="Blues", colorbar=False)
ax.set_title("TalentScope Demand Model - Confusion Matrix (Test Set)")
plt.tight_layout()
cm_path = "static/images/confusion_matrix.png"
plt.savefig(cm_path, dpi=150)
plt.close(fig)

# 7. Save Trained Model & Evaluation Metrics JSON
os.makedirs("models/saved", exist_ok=True)
joblib.dump(best_model, "models/saved/job_demand_model.pkl")

metrics_payload = {
    "selected_model": "TF-IDF (1-2 n-grams) + Balanced Logistic Regression",
    "train_samples": int(len(X_train)),
    "test_samples": int(len(X_test)),
    "accuracy": best_accuracy,
    "class_distribution": {k: int(v) for k, v in y.value_counts().items()},
    "model_comparison": comparison_results,
    "per_class_metrics": {
        label: {
            "precision": round(detailed_report[label]["precision"] * 100, 2),
            "recall": round(detailed_report[label]["recall"] * 100, 2),
            "f1_score": round(detailed_report[label]["f1-score"] * 100, 2),
            "support": int(detailed_report[label]["support"])
        }
        for label in class_labels
    },
    "confusion_matrix": {
        "labels": class_labels,
        "matrix": cm.tolist()
    },
    "limitations": [
        "Labels are derived from posting frequency within the 830-record dataset rather than longitudinal hiring forecasts.",
        "Dataset exhibits natural class imbalance (~77% Low Demand single-posting titles), handled using class_weight='balanced'.",
        "Because exact title strings can repeat across train and test splits, high test accuracy reflects keyword/title pattern learning rather than general macro-economic forecasting."
    ]
}

with open("models/saved/model_metrics.json", "w", encoding="utf-8") as f:
    json.dump(metrics_payload, f, indent=2)

print(f"\nConfusion matrix saved to: {cm_path}")
print("Model & metrics saved successfully to: models/saved/")
