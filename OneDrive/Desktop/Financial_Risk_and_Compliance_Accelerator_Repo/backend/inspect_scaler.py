import joblib
import numpy as np

scaler = joblib.load(r"models/scaler.joblib")

print("✅ Scaler loaded successfully.")
print(f"Type: {type(scaler)}")

# Check attributes that might hold column info
attrs = [a for a in dir(scaler) if not a.startswith("_")]
print("\nAvailable attributes:\n", attrs)

# Try to extract feature names or related data
for attr in ["feature_names_in_", "n_features_in_", "mean_", "var_", "scale_"]:
    if hasattr(scaler, attr):
        value = getattr(scaler, attr)
        print(f"\n🔹 {attr}: type={type(value)}, shape={getattr(value, 'shape', None)}")
        if isinstance(value, (list, np.ndarray)) and len(value) < 30:
            print(f"Values: {value}")

# Check if feature names might be stored in a dict or extra property
if hasattr(scaler, "__dict__"):
    print("\nExtra keys in scaler.__dict__:\n", list(scaler.__dict__.keys()))