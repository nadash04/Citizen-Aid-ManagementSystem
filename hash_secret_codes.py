import pandas as pd
import hashlib

def hash_secret(secret_code):
    salt = "citizen_aid_system_2024"
    return hashlib.sha256((secret_code + salt).encode('utf-8')).hexdigest()

df = pd.read_csv("citizens_data.csv", encoding="utf-8")

if "secret_code_hash" in df.columns:
    df["secret_code_hash"] = df["secret_code_hash"].apply(hash_secret)
    df.to_csv("citizens_data.csv", index=False, encoding="utf-8")
    print("✓ Hashing complete! File updated.")
else:
    print("✗ Column 'secret_code_hash' not found in the file.")
