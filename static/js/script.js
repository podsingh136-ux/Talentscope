// Store chart instances so they can be cleanly updated when filters change
const chartInstances = {};

function renderChart(canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (chartInstances[canvasId]) {
        chartInstances[canvasId].destroy();
    }

    chartInstances[canvasId] = new Chart(canvas, config);
}

// Populate State and Skill dropdowns from backend
async function loadFilterOptions() {
    try {
        const res = await fetch("/api/filter-options");
        if (!res.ok) return;

        const data = await res.json();
        const stateSelect = document.getElementById("stateFilter");
        const skillSelect = document.getElementById("skillFilter");

        data.states.forEach(state => {
            const opt = document.createElement("option");
            opt.value = state;
            opt.textContent = state;
            stateSelect.appendChild(opt);
        });

        data.skills.forEach(skill => {
            const opt = document.createElement("option");
            opt.value = skill;
            opt.textContent = skill;
            skillSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load filter options:", err);
    }
}

// Render all KPI cards, Trend Highlights, and all 8 Charts from a unified payload
function updateDashboardUI(data, filterLabel = "Showing All 830 Jobs") {
    // Update Filter Status Badge
    const statusBadge = document.getElementById("activeFilterStatus");
    if (statusBadge) {
        statusBadge.textContent = filterLabel;
    }

    // Update KPI Cards
    document.getElementById("totalJobs").textContent = data.total_jobs;
    document.getElementById("totalSkills").textContent = data.skills_tracked;
    document.getElementById("totalRoles").textContent = data.total_roles;
    document.getElementById("totalLocations").textContent = data.total_locations;

    // 1. Top Demanded Skills Chart
    renderChart("skillsChart", {
        type: "bar",
        data: {
            labels: data.skills.labels,
            datasets: [{
                label: "Job Title Mentions",
                data: data.skills.values,
                backgroundColor: "#3b82f6",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // 2. Job Role Distribution Chart
    renderChart("rolesChart", {
        type: "doughnut",
        data: {
            labels: data.roles.labels,
            datasets: [{
                data: data.roles.values,
                backgroundColor: ["#2563eb", "#8b5cf6", "#10b981", "#f59e0b", "#64748b"]
            }]
        },
        options: { responsive: true }
    });

    // 3. State-wise Job Demand Chart
    renderChart("stateChart", {
        type: "bar",
        data: {
            labels: data.state_demand.labels,
            datasets: [{
                label: "Job Postings",
                data: data.state_demand.values,
                backgroundColor: "#6366f1",
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            indexAxis: "y",
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });

    // 4. State-wise Average Monthly Salary Chart
    renderChart("salaryChart", {
        type: "bar",
        data: {
            labels: data.salary_analysis.labels,
            datasets: [{
                label: "Average Monthly Salary (₹)",
                data: data.salary_analysis.values,
                backgroundColor: "#10b981",
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return "₹" + context.parsed.y.toLocaleString("en-IN");
                        }
                    }
                }
            },
            scales: { y: { beginAtZero: true } }
        }
    });

    // 5. Top 10 In-Demand Skills Chart
    renderChart("topSkillsChart", {
        type: "bar",
        data: {
            labels: data.top_skills.labels,
            datasets: [{
                label: "Job Postings",
                data: data.top_skills.values,
                backgroundColor: "#8b5cf6",
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: "y",
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true } }
        }
    });

    // Update Trend Highlight Cards
    const totalWork = data.work_mode.values.reduce((a, b) => a + b, 0);
    const remoteCount = data.work_mode.values[1] || 0;
    const remotePct = totalWork ? ((remoteCount / totalWork) * 100).toFixed(1) : "0.0";
    document.getElementById("remoteShareText").textContent = `${remotePct}% Remote Jobs`;
    document.getElementById("remoteShareSub").textContent =
        `${data.work_mode.values[0]} On-site vs ${remoteCount} Remote postings`;

    const totalLevels = data.role_levels.values.reduce((a, b) => a + b, 0);
    const fresherCount = data.role_levels.values[0] || 0;
    const fresherPct = totalLevels ? ((fresherCount / totalLevels) * 100).toFixed(1) : "0.0";
    document.getElementById("fresherShareText").textContent = `${fresherPct}% Entry-Level`;
    document.getElementById("fresherShareSub").textContent =
        `${fresherCount} Fresher / Trainee / Intern openings`;

    const maxSalCount = Math.max(...data.salary_brackets.values);
    if (maxSalCount > 0) {
        const maxSalaryIdx = data.salary_brackets.values.indexOf(maxSalCount);
        document.getElementById("topBracketText").textContent =
            data.salary_brackets.labels[maxSalaryIdx];
        document.getElementById("topBracketSub").textContent =
            `${maxSalCount} postings in this salary slab`;
    } else {
        document.getElementById("topBracketText").textContent = "No Salary Data";
        document.getElementById("topBracketSub").textContent = "No disclosed salaries in current filter";
    }

    // 6. Work Mode Chart (Pie)
    renderChart("workModeChart", {
        type: "pie",
        data: {
            labels: data.work_mode.labels,
            datasets: [{
                data: data.work_mode.values,
                backgroundColor: ["#2563eb", "#f59e0b"]
            }]
        },
        options: { responsive: true }
    });

    // 7. Monthly Salary Brackets Chart (Bar)
    renderChart("salaryBracketChart", {
        type: "bar",
        data: {
            labels: data.salary_brackets.labels,
            datasets: [{
                label: "Job Postings",
                data: data.salary_brackets.values,
                backgroundColor: "#10b981",
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // 8. Hiring by Experience Level Chart (Doughnut)
    renderChart("roleLevelChart", {
        type: "doughnut",
        data: {
            labels: data.role_levels.labels,
            datasets: [{
                data: data.role_levels.values,
                backgroundColor: ["#8b5cf6", "#3b82f6", "#ec4899"]
            }]
        },
        options: { responsive: true }
    });
}

// Fetch filtered (or full) dataset and update dashboard
async function applyDashboardFilters() {
    const state = document.getElementById("stateFilter").value;
    const skill = document.getElementById("skillFilter").value;
    const role = document.getElementById("roleFilter").value.trim();
    const minSalary = document.getElementById("salaryFilter").value;

    const params = new URLSearchParams();
    if (state) params.append("state", state);
    if (skill) params.append("skill", skill);
    if (role) params.append("role", role);
    if (minSalary) params.append("min_salary", minSalary);

    try {
        const url = params.toString()
            ? `/api/filtered-data?${params.toString()}`
            : "/api/filtered-data";

        const response = await fetch(url);
        if (!response.ok) throw new Error("Filtered data API failed");

        const data = await response.json();

        const activeParts = [];
        if (state) activeParts.push(`State: ${state}`);
        if (skill) activeParts.push(`Skill: ${skill}`);
        if (role) activeParts.push(`Role: "${role}"`);
        if (minSalary) activeParts.push(`Min ₹${Number(minSalary).toLocaleString("en-IN")}`);

        const label = activeParts.length > 0
            ? `Filtered (${data.total_jobs} jobs) — ${activeParts.join(" | ")}`
            : `Showing All ${data.total_jobs} Jobs`;

        updateDashboardUI(data, label);
    } catch (error) {
        console.error("Filter Error:", error);
    }
}

function resetDashboardFilters() {
    document.getElementById("stateFilter").value = "";
    document.getElementById("skillFilter").value = "";
    document.getElementById("roleFilter").value = "";
    document.getElementById("salaryFilter").value = "";
    applyDashboardFilters();
}

// Fetch and render Advanced Data Analytics
async function loadAdvancedAnalytics() {
    try {
        const res = await fetch("/api/advanced-analytics");
        if (!res.ok) throw new Error("Advanced analytics API failed");

        const data = await res.json();
        const sal = data.salary_comparison;

        // Update Salary Metric Boxes
        document.getElementById("meanSalaryVal").textContent =
            "₹" + Number(sal.overall_mean).toLocaleString("en-IN");
        document.getElementById("medianSalaryVal").textContent =
            "₹" + Number(sal.overall_median).toLocaleString("en-IN");
        document.getElementById("modeSalaryVal").textContent =
            `₹${Math.round(sal.onsite_avg).toLocaleString("en-IN")} / ₹${Math.round(sal.remote_avg).toLocaleString("en-IN")}`;

        const totalRecs = sal.disclosed_count + sal.undisclosed_count;
        const pct = totalRecs ? ((sal.disclosed_count / totalRecs) * 100).toFixed(1) : "0.0";
        document.getElementById("disclosedRateVal").textContent = `${pct}%`;
        document.getElementById("disclosedRateSub").textContent =
            `${sal.disclosed_count} disclosed vs ${sal.undisclosed_count} undisclosed`;

        // 9. Functional Domain Chart (Horizontal Bar)
        renderChart("domainChart", {
            type: "bar",
            data: {
                labels: data.domain_distribution.labels,
                datasets: [{
                    label: "Job Postings",
                    data: data.domain_distribution.values,
                    backgroundColor: "#2563eb",
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                indexAxis: "y",
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });

        // 10. Average Monthly Salary by Skill Chart (Bar)
        renderChart("skillSalaryChart", {
            type: "bar",
            data: {
                labels: data.skill_salary.labels,
                datasets: [{
                    label: "Avg Monthly Salary (₹)",
                    data: data.skill_salary.values,
                    backgroundColor: "#10b981",
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return "₹" + context.parsed.y.toLocaleString("en-IN");
                            }
                        }
                    }
                },
                scales: { y: { beginAtZero: true } }
            }
        });

        // Populate Automated Key Insights List
        const listEl = document.getElementById("automatedInsightsList");
        listEl.innerHTML = "";
        data.key_insights.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item;
            listEl.appendChild(li);
        });

    } catch (error) {
        console.error("Advanced Analytics Error:", error);
    }
}

// Fetch and render ML Evaluation Metrics & Model Comparison
async function loadMLMetrics() {
    try {
        const res = await fetch("/api/ml-metrics");
        if (!res.ok) return;

        const data = await res.json();
        const m = data.metrics;

        const subtitleEl = document.getElementById("mlModelSubtitle");
        if (subtitleEl) {
            subtitleEl.textContent =
                `Selected: ${m.selected_model} | Accuracy: ${m.accuracy}% (${m.train_samples} train / ${m.test_samples} test)`;
        }

        // Populate Model Comparison Table
        const compBody = document.querySelector("#modelComparisonTable tbody");
        if (compBody) {
            compBody.innerHTML = "";
            m.model_comparison.forEach(row => {
                const tr = document.createElement("tr");
                if (row.model.includes("Logistic Regression")) {
                    tr.classList.add("selected-row");
                }
                tr.innerHTML = `
                    <td>${escapeHTML(row.model)}</td>
                    <td>${Number(row.accuracy).toFixed(2)}%</td>
                    <td>${Number(row.macro_f1).toFixed(2)}%</td>
                `;
                compBody.appendChild(tr);
            });
        }

        // Populate Per-Class Classification Report Table
        const classBody = document.querySelector("#classReportTable tbody");
        if (classBody) {
            classBody.innerHTML = "";
            Object.entries(m.per_class_metrics).forEach(([label, vals]) => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${escapeHTML(label)}</td>
                    <td>${Number(vals.precision).toFixed(2)}%</td>
                    <td>${Number(vals.recall).toFixed(2)}%</td>
                    <td>${Number(vals.f1_score).toFixed(2)}%</td>
                    <td>${vals.support}</td>
                `;
                classBody.appendChild(tr);
            });
        }

        // Populate Limitations Box
        const limBox = document.getElementById("mlLimitationsBox");
        if (limBox && m.limitations) {
            limBox.innerHTML = `
                <strong>Model Methodology & Dataset Limitations:</strong>
                <ul>
                    ${m.limitations.map(item => `<li>${escapeHTML(item)}</li>`).join("")}
                </ul>
            `;
        }
    } catch (error) {
        console.error("ML Metrics Error:", error);
    }
}

// Initialize Dashboard
async function initDashboard() {
    await loadFilterOptions();
    await applyDashboardFilters();
    await loadAdvancedAnalytics();
    await loadMLMetrics();

    document.getElementById("applyFiltersBtn").addEventListener("click", applyDashboardFilters);
    document.getElementById("resetFiltersBtn").addEventListener("click", resetDashboardFilters);

    // Allow Enter key in Role filter
    document.getElementById("roleFilter").addEventListener("keypress", function(e) {
        if (e.key === "Enter") applyDashboardFilters();
    });

    // Allow Enter key in ML Prediction input
    const mlInput = document.getElementById("jobTitleInput");
    if (mlInput) {
        mlInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") predictDemand();
        });
    }

    // Allow Enter key in Skill Recommender input
    const skillsInput = document.getElementById("userSkillsInput");
    if (skillsInput) {
        skillsInput.addEventListener("keypress", function(e) {
            if (e.key === "Enter") recommendJobs();
        });
    }
    setupSidebarNavigation();

    console.log("TalentScope Interactive Dashboard Loaded Successfully!");
}

initDashboard();


// ========================================
// AI JOB DEMAND PREDICTION
// ========================================

async function predictDemand() {

    const jobTitle = document
        .getElementById("jobTitleInput")
        .value.trim();

    const resultBox = document.getElementById("predictionResult");

    const predictBtn = document.getElementById("predictBtn");


    // Validate Input
    if (!jobTitle) {

        resultBox.innerHTML = "Please enter a job title!";

        return;
    }


    predictBtn.disabled = true;

    predictBtn.innerText = "Predicting...";

    resultBox.innerHTML = "Analyzing job title...";


    try {

        const response = await fetch("/api/predict-demand", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                job_title: jobTitle
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(data.message || "Prediction failed");

        }


        // Display Prediction Result
        resultBox.innerHTML = `

            <div class="prediction-output">

                <p>
                    Job Title: ${escapeHTML(data.job_title)}
                </p>

                <h3>
                    Predicted Demand:
                    ${escapeHTML(data.predicted_demand)}
                </h3>

                <p>
                    Model Confidence:
                    ${Number(data.confidence).toFixed(2)}%
                </p>

                <div class="confidence-bar">

                    <div
                        class="confidence-fill"
                        style="width: ${Math.max(0, Math.min(100, Number(data.confidence)))}%">
                    </div>

                </div>

            </div>

        `;


    }

    catch (error) {

        resultBox.innerHTML =
            "Error: " + escapeHTML(error.message);

    }

    finally {

        predictBtn.disabled = false;

        predictBtn.innerText = "Predict Demand";

    }

}


// ========================================
// SKILL-BASED JOB RECOMMENDATION SYSTEM
// ========================================

function fillSkillSample(sampleText) {
    const input = document.getElementById("userSkillsInput");
    if (input) {
        input.value = sampleText;
        recommendJobs();
    }
}

async function recommendJobs() {
    const skillsInput = document.getElementById("userSkillsInput");
    const resultsBox = document.getElementById("recommendationResults");
    const btn = document.getElementById("recommendBtn");

    const skillsText = skillsInput.value.trim();

    if (!skillsText) {
        resultsBox.innerHTML = `<p class="rec-summary" style="color:#dc2626;">Please enter at least one skill (e.g. Python, Data Analysis).</p>`;
        return;
    }

    btn.disabled = true;
    btn.innerText = "Searching...";
    resultsBox.innerHTML = `<p class="rec-summary">Matching your skills against dataset job openings...</p>`;

    try {
        const response = await fetch("/api/recommend-jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skills: skillsText })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Recommendation failed");
        }

        if (!data.recommendations || data.recommendations.length === 0) {
            resultsBox.innerHTML = `
                <div class="ml-limitations" style="margin-top:16px;">
                    <strong>No direct job title matches found for "${escapeHTML(skillsText)}".</strong>
                    <p style="margin-top:6px;">
                        Note: This dataset contains job titles without full job descriptions.
                        Try broader skills found in titles such as:
                        <strong>${escapeHTML(data.top_market_skills.join(", "))}</strong>.
                    </p>
                </div>
            `;
            return;
        }

        const cardsHTML = data.recommendations.map(rec => `
            <div class="rec-card">
                <div class="rec-card-header">
                    <h4>${escapeHTML(rec.job_title)}</h4>
                    <span class="rec-salary">${escapeHTML(rec.salary)}</span>
                </div>
                <div class="rec-meta">Location: ${escapeHTML(rec.location)}</div>
                <p class="rec-reason">${escapeHTML(rec.reason)}</p>
                <div class="rec-tags">
                    ${rec.matched_skills.map(s => `<span class="tag-matched">Matched: ${escapeHTML(s)}</span>`).join("")}
                    ${rec.demanded_skills.map(s => `<span class="tag-upskill">+ Learn: ${escapeHTML(s)}</span>`).join("")}
                </div>
            </div>
        `).join("");

        resultsBox.innerHTML = `
            <p class="rec-summary">
                Found ${data.total_matches} real job opening(s) matching [${escapeHTML(data.input_skills.join(", "))}] — Showing top ${data.recommendations.length}:
            </p>
            <div class="rec-grid">
                ${cardsHTML}
            </div>
            <p style="font-size:11px; color:#64748b; margin-top:12px;">
                ${escapeHTML(data.note)}
            </p>
        `;

    } catch (error) {
        resultsBox.innerHTML = `<p class="rec-summary" style="color:#dc2626;">Error: ${escapeHTML(error.message)}</p>`;
    } finally {
        btn.disabled = false;
        btn.innerText = "Find Matching Roles";
    }
}


// ========================================
// HTML SECURITY FUNCTION
// ========================================

function escapeHTML(value) {

    return String(value).replace(/[&<>"']/g, function(char) {

        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[char];

    });

}
// ========================================
// REPORT EXPORT (CSV & PDF WITH FILTERS)
// ========================================

function downloadReport(format) {
    const state = document.getElementById("stateFilter")?.value || "";
    const skill = document.getElementById("skillFilter")?.value || "";
    const role = document.getElementById("roleFilter")?.value.trim() || "";
    const minSalary = document.getElementById("salaryFilter")?.value || "";

    const params = new URLSearchParams();
    if (state) params.append("state", state);
    if (skill) params.append("skill", skill);
    if (role) params.append("role", role);
    if (minSalary) params.append("min_salary", minSalary);

    const query = params.toString();
    const url = query ? `/api/export/${format}?${query}` : `/api/export/${format}`;
    window.location.href = url;
}


// ========================================
// SIDEBAR ACTIVE NAVIGATION
// ========================================

function setupSidebarNavigation() {
    const navLinks = document.querySelectorAll("#sidebarNav .nav-link");
    navLinks.forEach(link => {
        link.addEventListener("click", function() {
            navLinks.forEach(item => item.classList.remove("active"));
            this.classList.add("active");
        });
    });
}
