import streamlit as st
import requests
import json
import pandas as pd
import numpy as np
from io import StringIO
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# --- 1. CONFIGURATION ---
# Set the page configuration for a professional look
st.set_page_config(
    page_title="Integrated Credit Risk Assessment System",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Endpoint
API_URL = "https://integrated-risk-api-670590024965.us-central1.run.app/score/credit"

# --- 3. AUTHENTICATION FUNCTION (FINAL FIX: Using Service Account Key) ---

@st.cache_resource
def get_auth_token(audience: str, key_file_path: str = 'sa_key.json'):
    """Generates a Google Identity Token using a Service Account Key File."""
    try:
        # Check if the key file exists in the Streamlit app folder
        if not Path(key_file_path).exists():
            st.error(f"🚨 Authentication Failed: Key file not found at {key_file_path}")
            return None

        # Load credentials from the JSON file
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            key_file_path,
            target_audience=audience
        )
        
        # Get the ID Token (required by Cloud Run Invoker)
        auth_req = Request()
        credentials.refresh(auth_req)

        st.info("Authentication token generated successfully via Service Account.")
        return credentials.token
        
    except Exception as e:
        st.error(f"🚨 Critical Auth Failure: Check key file contents and 'Cloud Run Invoker' role. Details: {e}")
        return None

# --- 2. TEST CASES DATA (Confirmed from analysis of test_api.py) ---
TEST_CASES = {
    "Select a Test Case...": None,
    "Case 1: High Credit Risk (Review Expected)": {
        "SK_ID_CURR": 100001, "AMT_INCOME_TOTAL": 100000.0, "AMT_CREDIT": 900000.0,
        "AMT_ANNUITY": 40000.0, "AMT_GOODS_PRICE": 800000.0, "DAYS_BIRTH": -10000,
        "DAYS_EMPLOYED": -300, "CODE_GENDER": "M", "NAME_INCOME_TYPE": "Working",
        "ORGANIZATION_TYPE": "Transport: type 3", "EXT_SOURCE_1": 0.01,
        "EXT_SOURCE_2": 0.01, "EXT_SOURCE_3": 0.01
    },
    "Case 2: Low Risk (Approve Expected)": {
        "SK_ID_CURR": 100002, "AMT_INCOME_TOTAL": 650000.0, "AMT_CREDIT": 90000.0,
        "AMT_ANNUITY": 10000.0, "AMT_GOODS_PRICE": 80000.0, "DAYS_BIRTH": -13000,
        "DAYS_EMPLOYED": -5000, "CODE_GENDER": "F", "NAME_INCOME_TYPE": "Businessman",
        "ORGANIZATION_TYPE": "Business Entity Type 3", "EXT_SOURCE_1": 0.9,
        "EXT_SOURCE_2": 0.9, "EXT_SOURCE_3": 0.9
    },
    "Case 3: Mixed Risk (Review Expected)": {
        "SK_ID_CURR": 100003, "AMT_INCOME_TOTAL": 250000.0, "AMT_CREDIT": 250000.0,
        "AMT_ANNUITY": 18000.0, "AMT_GOODS_PRICE": 240000.0, "DAYS_BIRTH": -18000,
        "DAYS_EMPLOYED": -1000, "CODE_GENDER": "M", "NAME_INCOME_TYPE": "Working",
        "ORGANIZATION_TYPE": "Transport: type 2", "EXT_SOURCE_1": 0.0,
        "EXT_SOURCE_2": 0.7, "EXT_SOURCE_3": 0.65
    },
    "Case 4: High All-Risk (Reject Expected)": { # Triggers all three high risk conditions
        "SK_ID_CURR": 100004, "AMT_INCOME_TOTAL": 50000.0, "AMT_CREDIT": 600000.0,
        "AMT_ANNUITY": 28000.0, "AMT_GOODS_PRICE": 500000.0, "DAYS_BIRTH": -11000,
        "DAYS_EMPLOYED": -1200, "CODE_GENDER": "F", "NAME_INCOME_TYPE": "Working",
        "ORGANIZATION_TYPE": "Trade: type 7", "EXT_SOURCE_1": 0.05,
        "EXT_SOURCE_2": 0.05, "EXT_SOURCE_3": 0.05
    },
    "Case 5: High AML Only (Review Expected)": { # Triggers AML High, but Credit/Fraud Low
        "SK_ID_CURR": 100005, "AMT_INCOME_TOTAL": 50000.0, "AMT_CREDIT": 100000.0,
        "AMT_ANNUITY": 15000.0, "AMT_GOODS_PRICE": 90000.0, "DAYS_BIRTH": -15000,
        "DAYS_EMPLOYED": -2500, "CODE_GENDER": "M", "NAME_INCOME_TYPE": "State servant",
        "ORGANIZATION_TYPE": "Government", "EXT_SOURCE_1": 0.9,
        "EXT_SOURCE_2": 0.9, "EXT_SOURCE_3": 0.9
    }
}

# --- 3. INITIAL STATE AND RESET FUNCTIONS ---
def initialize_state():
    """Initializes or resets all input fields to their default values."""
    st.session_state["SK_ID_CURR"] = 100001
    st.session_state["AMT_INCOME_TOTAL"] = 250000.0
    st.session_state["AMT_CREDIT"] = 300000.0
    st.session_state["AMT_ANNUITY"] = 15000.0
    st.session_state["AMT_GOODS_PRICE"] = 250000.0
    st.session_state["DAYS_BIRTH"] = -10000
    st.session_state["DAYS_EMPLOYED"] = -2000
    st.session_state["EXT_SOURCE_1"] = 0.5
    st.session_state["EXT_SOURCE_2"] = 0.5
    st.session_state["EXT_SOURCE_3"] = 0.5
    st.session_state["CODE_GENDER"] = "F"
    st.session_state["NAME_INCOME_TYPE"] = "Working"
    st.session_state["ORGANIZATION_TYPE"] = "Business Entity Type 3"
    st.session_state["FINAL_DECISION"] = None # To clear the result display

def apply_test_case():
    """Applies the selected test case values to the input state."""
    case_name = st.session_state.test_case_selector
    if TEST_CASES.get(case_name):
        case = TEST_CASES[case_name]
        for key, value in case.items():
            if key in st.session_state:
                st.session_state[key] = value
        st.session_state["FINAL_DECISION"] = None # Clear results on new case load
        st.toast(f"Test case '{case_name}' loaded successfully!", icon="✅")

# Ensure state is initialized on first run
if "SK_ID_CURR" not in st.session_state:
    initialize_state()

# --- 4. UI Helper Functions ---
def get_decision_banner(decision: str):
    """Returns the banner details (icon, color, message) based on the final decision."""
    decision_map = {
        "Approve": ("✅ APPROVED", "#4CAF50", "This applicant meets the low-risk criteria across all models."),
        "Review": ("⚠️ FOR REVIEW", "#FFC107", "Further manual underwriting is required due to mixed or elevated risk in one or more models."),
        "Reject": ("❌ REJECTED", "#F44336", "This application presents an unacceptably high risk profile (Credit, Fraud, and/or AML)."),
    }
    banner, color, message = decision_map.get(decision, ("❓ UNKNOWN", "gray", "Decision status is unclear."))
    return banner, color, message

def get_risk_metric_style(value: float, high_risk_threshold: float):
    """Returns the color for a risk score metric (Green for low, Red for high)."""
    # Streamlit's 'inverse' is Red for metric delta, 'normal' is Green.
    if value >= high_risk_threshold:
        return "inverse"
    return "normal"

def get_aml_color_code(aml_suspicion: str):
    """Returns the color code for the AML suspicion level."""
    if aml_suspicion == "High":
        return "#F44336" # Red
    elif aml_suspicion == "Neutral":
        return "#FFC107" # Yellow/Orange
    return "#4CAF50" # Green

# --- 5. MAIN APPLICATION UI ---

# Header Section
st.title("💰 Integrated Credit Risk Assessment System")
st.markdown("### Multi-Model Risk Analysis: Credit | Fraud | AML")
st.divider()

# --- Sidebar for Inputs (Section 1 & 2 UI) ---
with st.sidebar:
    st.header("👤 Applicant Data Input")

    # 2. QUICK TEST CASES
    st.subheader("Quick Test Cases")
    st.selectbox(
        "Load Pre-filled Case",
        options=list(TEST_CASES.keys()),
        key="test_case_selector",
        index=0,
        on_change=apply_test_case,
        help="Select a test case to automatically populate the input fields below."
    )
    st.button("Clear All Inputs", on_click=initialize_state, use_container_width=True)
    st.divider()

    # 1. USER INPUT SECTION - Numerical Inputs
    st.subheader("Required Features")

    col1, col2 = st.columns(2)
    with col1:
        st.number_input("SK_ID_CURR", min_value=1, key="SK_ID_CURR", format="%d")
    with col2:
        st.number_input(
            "DAYS_BIRTH", min_value=-25000, max_value=-5000, step=1,
            key="DAYS_BIRTH", format="%d",
            help="Age of applicant in days (negative value). E.g., -10000 days ≈ 27.4 years old."
        )

    st.slider("AMT_INCOME_TOTAL", min_value=50000.0, max_value=1000000.0, step=1000.0,
        key="AMT_INCOME_TOTAL", format="%.0f", help="Total income of the applicant. (Range: 50,000 - 1,000,000)"
    )
    st.slider("AMT_CREDIT (Loan Amount)", min_value=50000.0, max_value=1000000.0, step=1000.0,
        key="AMT_CREDIT", format="%.0f", help="Loan amount applied for. (Range: 50,000 - 1,000,000)"
    )
    st.slider("AMT_ANNUITY (Loan Annuity)", min_value=5000.0, max_value=50000.0, step=100.0,
        key="AMT_ANNUITY", format="%.0f", help="Annual payment amount. (Range: 5,000 - 50,000)"
    )
    st.slider("AMT_GOODS_PRICE", min_value=50000.0, max_value=1000000.0, step=1000.0,
        key="AMT_GOODS_PRICE", format="%.0f", help="Price of the goods/service. (Range: 50,000 - 1,000,000)"
    )
    st.number_input("DAYS_EMPLOYED", min_value=-10000, max_value=-100, step=1,
        key="DAYS_EMPLOYED", format="%d",
        help="How many days before the application the person started current employment (negative value). (Range: -10000 to -100)"
    )
    st.divider()

    # Categorical Inputs
    col3, col4 = st.columns(2)
    with col3:
        st.selectbox("CODE_GENDER", options=["M", "F"], key="CODE_GENDER")
    with col4:
        st.selectbox("NAME_INCOME_TYPE",
            options=["Working", "Businessman", "State servant", "Commercial associate", "Pensioner"],
            key="NAME_INCOME_TYPE"
        )
    st.selectbox("ORGANIZATION_TYPE",
        options=["Transport: type 3", "Business Entity Type 3", "Government", "Trade: type 7", "Transport: type 2"],
        key="ORGANIZATION_TYPE"
    )
    st.divider()

    # EXT_SOURCE Scores
    st.subheader("Credit Bureau Scores (External Sources)")
    help_text_ext = "Normalized score from an external data source (0.0 = worst, 1.0 = best). (Range: 0.0 - 1.0)"
    st.slider("EXT_SOURCE_1", min_value=0.0, max_value=1.0, step=0.01, key="EXT_SOURCE_1", help=help_text_ext)
    st.slider("EXT_SOURCE_2", min_value=0.0, max_value=1.0, step=0.01, key="EXT_SOURCE_2", help=help_text_ext)
    st.slider("EXT_SOURCE_3", min_value=0.0, max_value=1.0, step=0.01, key="EXT_SOURCE_3", help=help_text_ext)
    st.divider()

    # Submission Button
    submit_button = st.button("Predict Credit Risk", key="submit_button", type="primary", use_container_width=True)

# --- 6. API INTEGRATION and RESULTS DISPLAY ---
if submit_button:
    # Request Preparation
    input_data = {key: st.session_state[key] 
                  for key in st.session_state.keys() 
                  if key not in ["test_case_selector", "FINAL_DECISION"]}

    # Convert values to required types to avoid 400 errors from API
    
    # Ensure IDs and DAYS are integers (required by the backend logic)
    input_data["SK_ID_CURR"] = int(input_data["SK_ID_CURR"])
    input_data["DAYS_BIRTH"] = int(input_data["DAYS_BIRTH"])
    input_data["DAYS_EMPLOYED"] = int(input_data["DAYS_EMPLOYED"])

    # Ensure large monetary values are floats (as they are in the JSON samples)
    input_data["AMT_INCOME_TOTAL"] = float(input_data["AMT_INCOME_TOTAL"])
    input_data["AMT_CREDIT"] = float(input_data["AMT_CREDIT"])
    input_data["AMT_ANNUITY"] = float(input_data["AMT_ANNUITY"])
    input_data["AMT_GOODS_PRICE"] = float(input_data["AMT_GOODS_PRICE"])

    # Ensure EXT_SOURCE values are explicitly floats
    input_data["EXT_SOURCE_1"] = float(input_data["EXT_SOURCE_1"])
    input_data["EXT_SOURCE_2"] = float(input_data["EXT_SOURCE_2"])
    input_data["EXT_SOURCE_3"] = float(input_data["EXT_SOURCE_3"])
    
    # Payload must be a JSON array of records, even for a single applicant
    payload = json.dumps([input_data])

    # --- 6. AUTHENTICATED API CALL (FIX FOR 503/Permissions) ---
    # The audience is the base URL without the endpoint path (e.g., https://service.run.app)
    AUDIENCE_URL = API_URL.rsplit('/', 1)[0]
    auth_token = get_auth_token(AUDIENCE_URL)

    # Check if the token was successfully generated
    if not auth_token:
        st.session_state["FINAL_DECISION"] = None
        st.stop()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}' # Send the token for authentication
    }

    try:
        with st.spinner("Analyzing applicant risk profile..."):
            response = requests.post(
                API_URL,
                data=payload,
                headers=headers, # Use the authenticated headers
                timeout=900
            )
            
            response.raise_for_status() # Check for HTTP errors

            # Get the result
            result = response.json()
            if not isinstance(result, list) or not result:
                st.error("API returned an unexpected response format. Expected a list of results.")
                st.session_state["FINAL_DECISION"] = None
            else:
                st.session_state["FINAL_DECISION"] = result[0]

    # Error Handling Block
    except requests.exceptions.Timeout:
        st.error("🚨 Request Timeout: The API took too long to respond. Please try again later.")
        st.session_state["FINAL_DECISION"] = None
    except requests.exceptions.ConnectionError:
        st.error("🚨 Network Error: Could not connect to the API. Check your internet connection or the API status.")
        st.session_state["FINAL_DECISION"] = None
    except requests.exceptions.HTTPError as e:
        st.error(f"🚨 API Error: The server returned status code {e.response.status_code}. (Expected 200)")
            
        # Attempt to parse the JSON response body to find the 'details' key
        try:
            error_response_json = response.json()
            error_details = error_response_json.get('details', 'No specific details provided by the server.')
        except:
            error_details = response.text # Fallback to raw text if not JSON

        st.warning("This is likely a missing data file on the API server.")
        with st.expander("Show Server Error Details (Look for '...bureau.csv' or similar):"):
            st.code(error_details)
        st.session_state["FINAL_DECISION"] = None
    except Exception as e:
        st.error(f"🚨 An unexpected error occurred: {e}")
        st.session_state["FINAL_DECISION"] = None

# --- RESULTS DISPLAY ---
if st.session_state.get("FINAL_DECISION"):
    results = st.session_state["FINAL_DECISION"]
    final_decision = results.get('FINAL_DECISION', 'Review')

    # Final Decision Banner
    banner, color_code, message = get_decision_banner(final_decision)
    st.markdown(f"""
        <div style="
            background-color: {color_code};
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        ">
            {banner}
        </div>
        <p style="text-align: center; font-style: italic; color: #555;">{message}</p>
    """, unsafe_allow_html=True)
    st.divider()

    st.subheader("Multi-Model Risk Scores (Threshold $\\ge 0.5$ is High Risk)")

    # Risk Score Cards
    colA, colB, colC = st.columns(3)

    # CREDIT RISK SCORE
    credit_score = results.get('CREDIT_RISK_SCORE', 0.0)
    colA.metric(
        label="Credit Default Probability (0-1)",
        value=f"{credit_score:.3f}",
        delta="High Risk: $\\ge 0.5$",
        delta_color=get_risk_metric_style(credit_score, 0.5)
    )

    # FRAUD PROBABILITY
    fraud_prob = results.get('FRAUD_PROBABILITY', 0.0)
    colB.metric(
        label="Fraud Risk Probability (0-1)",
        value=f"{fraud_prob:.3f}",
        delta="High Risk: $\\ge 0.5$",
        delta_color=get_risk_metric_style(fraud_prob, 0.5)
    )

    # AML SUSPICION
    aml_suspicion = results.get('AML_SUSPICION', 'Neutral')
    aml_color = get_aml_color_code(aml_suspicion)
    colC.markdown(
        f"""
        **AML Suspicion**
        <p style="
            background-color: {aml_color};
            color: white;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            font-size: 1.2em;
        ">{aml_suspicion}</p>
        """, unsafe_allow_html=True
    )
    st.divider()

    # Additional Details (Expandable Section)
    with st.expander("View Raw API Output and Export"):
        st.json(results)

        # Download Button
        json_data = json.dumps(results, indent=2)
        st.download_button(
            label="Download Results as JSON",
            data=json_data,
            file_name="risk_assessment_results.json",
            mime="application/json",
            use_container_width=True
        )

# Initial State
else:
    st.info("👈 Enter applicant data in the sidebar or load a test case, then click 'Predict Credit Risk' to run the multi-model assessment.")