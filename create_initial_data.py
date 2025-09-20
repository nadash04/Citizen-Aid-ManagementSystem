# create_initial_data.py - Script to populate initial data from external CSV

import backend_functions as be
print("USING BACKEND FILE:", be.__file__)

import datetime
import pandas as pd

def create_initial_data():
    """Loads citizens from an external CSV and sets up initial data."""
    
    print("Setting up CSV files...")
    be.setup_csv_files()
    
    print("Creating initial admin accounts...")
    
    admins_data = [
        {"username": "admin", "password": "admin123", "full_name": "System Administrator", "organization_id": "ORG001", "role": "admin"},
        {"username": "manager", "password": "manager123", "full_name": "Aid Manager", "organization_id": "ORG001", "role": "manager"},
        {"username": "supervisor", "password": "super123", "full_name": "Field Supervisor", "organization_id": "ORG002", "role": "supervisor"}
    ]
    
    for admin_data in admins_data:
        success = be.register_admin_csv(
            username=admin_data["username"],
            password=admin_data["password"],
            full_name=admin_data["full_name"],
            organization_id=admin_data["organization_id"],
            role=admin_data["role"]
        )
        if success:
            print(f"✓ Created admin: {admin_data['username']}")
        else:
            print(f"✗ Failed to create admin: {admin_data['username']}")

    print("\nImporting citizen data from 'citizens_data.csv'...")

    try:
        df = pd.read_csv('citizens_data.csv', encoding='utf-8')
        citizens_data = df.to_dict(orient='records')
    except Exception as e:
        print(f"✗ Error reading citizens_data.csv: {e}")
        return

    citizen_ids = []
    for citizen_data in citizens_data:
        # Ensure optional fields exist
        citizen_data.setdefault("is_active", "True")
        citizen_data.setdefault("registration_date", datetime.datetime.now().strftime("%Y-%m-%d"))
        citizen_data.setdefault("latitude", "")
        citizen_data.setdefault("longitude", "")
        
        registered_record = be.register_citizen_csv(citizen_data)
        if registered_record:
            citizen_id = registered_record.get("id")
            citizen_ids.append(citizen_id)
            print(f"✓ Created citizen: {citizen_data.get('full_name', 'N/A')} (ID: {citizen_id})")
        else:
            print(f"✗ Failed to create citizen: {citizen_data.get('full_name', 'N/A')}")

    print(f"\nCitizen Accounts Created: {len(citizen_ids)}")
    
    print("\nSkipping aid history and messages setup (optional)\n")
    print("="*60)
    print("DATA IMPORT FROM EXTERNAL CSV COMPLETED!")
    print("="*60)
    print("\nAdmin Accounts Created:")
    print("Username: admin, Password: admin123")
    print("Username: manager, Password: manager123") 
    print("Username: supervisor, Password: super123")

if __name__ == "__main__":
    create_initial_data()

