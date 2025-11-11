# 🏆 Financial Risk and Compliance Accelerator (FRCA)

## 🎯 Project Goal & Integrated Policy
The FRCA project deploys an integrated, real-time risk assessment API to generate automated lending decisions across **three key risk pillars**: Credit, Fraud, and Anti-Money Laundering (AML).

* **Decision Policy:**
    * **Approve:** All three models return low risk (Green).
    * **Review:** One or two models return medium/high risk (Yellow/Red). Requires manual compliance review.
    * **Reject:** All three models return high risk, or a critical Fraud/AML flag is raised.

## 🚀 Deployed Endpoints
| Component | Status | URL/Access Point |
| :--- | :--- | :--- |
| **Scoring API (Backend)** | Deployed & Warmed | `https://integrated-risk-api-670590024965.us-central1.run.app` |
| **Streamlit UI (Frontend)** | Local Demo | Run via instructions below |

## 💻 Technical Stack
* **Frontend:** Streamlit, Python (`requests`, `google-auth`)
* **Backend API:** Flask, Pandas, LightGBM, Random Forest, Joblib
* **Deployment:** Google Cloud Run (Containerized via Docker)
* **Data Assets:** 3 models and 5 feature reference CSVs are globally loaded for cold start mitigation.

## 📂 Repository Structure

The project assets are organized into dedicated folders for clarity and separation of concerns:

| Folder | Contents | Purpose |
| :--- | :--- | :--- |
| **`backend/`** | `app.py`, `Dockerfile`, `models/`, `requirements.txt` | **Cloud Run Scoring Service.** (Code for the deployed API). |
| **`frontend/`** | `streamlit_app.py`, `requirements.txt` | **Streamlit UI.** (Code for the local live demo). |
| **`documentation/`** | Presentation, Report, Diagram | Formal submission assets. |
| **`notebooks/`** | Analysis `.ipynb` files | Developmental work and feature engineering proof-of-concept. |

## ⚙️ How to Run the Live Demonstration
1.  **Clone the repository:** `git clone https://github.com/shwetageras/Financial_Risk_and_Compliance_Accelerator_Repo.git`
2.  **Navigate to the frontend:** `cd frontend`
3.  **Install dependencies:** `pip install -r requirements.txt`
4.  **Run the Streamlit application:** `streamlit run streamlit_app.py`
5.  **Test:** Enter sample customer data in the UI. The application will securely call the deployed Cloud Run API endpoint and display the Integrated Decision (Approve/Review/Reject).
