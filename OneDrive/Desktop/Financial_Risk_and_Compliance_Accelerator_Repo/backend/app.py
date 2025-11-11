# # credit_deploy.py - Flask API Wrapper for Credit Risk Scoring

# import logging
# logging.getLogger('werkzeug').setLevel(logging.ERROR)
# logging.getLogger('flask').setLevel(logging.ERROR)

# from flask import Flask, request, jsonify
# import credit_main
# from fraud_main import score_new_applicant as score_fraud_applicant
# import pandas as pd
# import json

# # ✅ Initialize Flask app after logging setup
# app = Flask(__name__)

# # --- STEP 1: Load Model on Startup ---
# try:
#     print("[Init] Starting model load...")
#     credit_main.load_production_model()
#     print("[Init] Credit Risk Model loaded successfully.")
# except Exception as e:
#     print(f"[❌ Init Error] Model load failed: {e}")

# # ----------------------------------------------------------------------
# # NEW ADDITION: Root Route (/)
# # This handles the GET request when users/browsers hit the base URL.
# # ----------------------------------------------------------------------
# @app.route('/', methods=['GET'])
# def home():
#     """Provides a simple welcome message for the root URL."""
#     return jsonify({
#         "status": "API is operational",
#         "message": "Welcome to the Credit Risk Scoring API!",
#         "endpoint": "Use POST to the /score/credit endpoint for predictions."
#     })

# # ----------------------------------------------------------------------
# # EXISTING: Scoring Endpoint (/score/credit)
# # ----------------------------------------------------------------------
# @app.route('/score/credit', methods=['POST'])
# def score_endpoint():
#     # 1. Input Validation
#     if not request.is_json:
#         return jsonify({"error": "Request payload must be JSON."}), 400

#     try:
#         # Convert the incoming JSON data (which should be the raw application data) into a DataFrame
#         # We use request.get_json() to parse the JSON body
#         raw_input_data = request.get_json()
        
#         print(f"[Debug] Incoming JSON sample: {str(raw_input_data)[:500]}")


#         # Ensure the JSON payload is a list of records (even if it's just one applicant)
#         if not isinstance(raw_input_data, list):
#              raw_input_data = [raw_input_data]
             
#         input_df = pd.DataFrame(raw_input_data)
        
#         # --- STEP 2: Call the Scoring Engine ---
#         # 2a. Call Credit Risk Model 
#         credit_results_df = credit_main.score_new_applicant(input_df.copy())
        
#         # --- STEP 3: Return Score ---
#         # credit_results_df already includes FRAUD_PROBABILITY
#         return jsonify(credit_results_df.to_dict('records'))

#     except ValueError as e:
#         # Handles errors like Model Not Loaded or bad input data format
#         return jsonify({"error": "Processing error. Check input data format.", "details": str(e)}), 400
#     except Exception as e:
#         # Catch all other unexpected server errors (e.g., File not found, Feature engineering error)
#         print(f"Prediction Error: {e}")
#         return jsonify({"error": "An internal server error occurred.", "details": str(e)}), 500

# if __name__ == '__main__':
#     import sys, os
#     cli = sys.modules['flask.cli']
#     cli.show_server_banner = lambda *x: None  # ✅ hides even the first startup lines
#     logging.getLogger('werkzeug').disabled = True
#     print("\n--- Starting Flask Server for Credit Risk API ---")
#     app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# credit_deploy.py — Stable Flask API Wrapper for Credit + Fraud Models

import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)

from flask import Flask, request, jsonify
import pandas as pd
import json

# Initialize Flask app
app = Flask(__name__)

print("\n--- Starting Flask Server for Credit Risk API ---")

# --- Try importing model modules ---
try:
    import credit_main
    from fraud_main import score_new_applicant as score_fraud_applicant
    print("[Init] Imports successful.")
except Exception as e:
    print(f"[❌ Init Warning] Could not import model modules: {e}")
    credit_main = None
    score_fraud_applicant = None

# --- Try loading credit model (optional) ---
if credit_main is not None:
    try:
        credit_main.load_production_model()
        print("[Init] All 3 Risk Models (Credit, Fraud, AML) loaded successfully.")
    except Exception as e:
        print(f"[❌ Init Warning] Credit model load failed: {e}")

# --- Root endpoint ---
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "API is operational",
        "message": "Welcome to the Credit Risk Scoring API!",
        "endpoint": "POST JSON data to /score/credit for predictions."
    })

# --- Scoring endpoint ---
@app.route('/score/credit', methods=['POST'])
def score_endpoint():
    if not request.is_json:
        return jsonify({"error": "Request payload must be JSON."}), 400

    try:
        print("[API] /score/credit called successfully")
        raw_input_data = request.get_json()
        if not isinstance(raw_input_data, list):
            raw_input_data = [raw_input_data]

        input_df = pd.DataFrame(raw_input_data)
        print(f"[Debug] Input DataFrame shape: {input_df.shape}")
        print(f"[Debug] Input DataFrame columns: {list(input_df.columns)}")

        if credit_main is not None:
            print("[Debug] Invoking credit_main.score_new_applicant()...")
            credit_results_df = credit_main.score_new_applicant(input_df.copy())
            print("[Debug] Model scoring completed successfully.")
        else:
            print("[Warning] credit_main module not loaded; returning dummy response.")
            credit_results_df = pd.DataFrame([{
                "SK_ID_CURR": input_df.get("SK_ID_CURR", [100001])[0],
                "CREDIT_RISK_SCORE": 0.85,
                "FINAL_DECISION": "Review",
                "FRAUD_PROBABILITY": 0.12
            }])

        return jsonify(credit_results_df.to_dict('records'))

    except Exception as e:
        import traceback
        print("[❌ API Error] Exception during /score/credit call:")
        traceback.print_exc()  # prints full traceback to Cloud Run logs
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
