# TalentScope – Job Market Intelligence Platform

**Project Title:** Job Market Intelligence: Analyzing Industry Skill Demand and Employment Trends Using Data Analytics

## Overview
**TalentScope** is an end-to-end Data Analytics and Machine Learning web application built with **Python, Flask, Pandas, Scikit-learn, and Chart.js**. It processes Indian job market postings to uncover state-wise hiring demand, salary distributions, functional domain breakdowns, skill-to-pay trends, and role demand classifications.

## Key Features
- **Automated Data Cleaning Pipeline (`preprocessing/clean_dataset.py`):** Deduplicates raw job records (835 → 830 unique rows) and normalizes annual/monthly text salary ranges into standardized monthly INR values.
- **Interactive Analytics Dashboard:** Real-time filtering by **State/Location**, **Technical Skill**, **Job Role Keyword**, and **Minimum Monthly Salary** with dynamic Chart.js updates.
- **Employment Trends & Advanced Analytics:** Tracks On-site vs. Remote hiring splits, monthly salary brackets, fresher/trainee vs. experienced demand, functional domain categories, and Mean vs. Median monthly pay.
- **AI Job Demand Prediction (`models/saved/train_model.py`):** Uses **TF-IDF (1–2 n-grams) + Balanced Logistic Regression** (`85.54%` test accuracy, `82.22%` Macro F1) to classify job titles into *High Demand*, *Medium Demand*, or *Low Demand* with probability confidence bars, model comparison metrics, and a confusion matrix.
- **Skill-Based Job Recommender:** Matches user-entered skills against real dataset job openings with disclosed salary info, recommendation explanations, and complementary upskill suggestions.
- **CSV & PDF Report Export:** One-click downloadable CSV datasets and formatted A4 PDF analytics reports reflecting active dashboard filters.

## Project Structure
```text
TALENTSCOPE/
├── analytics/
│   └── analyze_jobs.py              # Generates summary CSV analytics reports
├── data/
│   ├── raw/job_market_india.csv     # Raw dataset (835 records)
│   └── processed/
│       ├── jobs_cleaned.csv         # Cleaned dataset (830 records)
│       └── analytics/               # Pre-aggregated CSV summaries
├── models/
│   └── saved/
│       ├── train_model.py           # ML training, comparison & confusion matrix generator
│       ├── job_demand_model.pkl     # Serialized TF-IDF + Logistic Regression pipeline
│       └── model_metrics.json       # Evaluation metrics & classification report
├── preprocessing/
│   ├── check_dataset.py             # Raw dataset inspection
│   └── clean_dataset.py             # Salary normalization & deduplication
├── static/
│   ├── css/style.css                # Responsive dashboard styling
│   ├── images/confusion_matrix.png  # Saved ML confusion matrix plot
│   └── js/script.js                 # Frontend API integration & Chart.js rendering
├── templates/
│   └── index.html                   # Main dashboard UI
├── app.py                           # Flask REST API & web server
├── requirements.txt                 # Python dependencies
└── README.md                        # Project documentation
