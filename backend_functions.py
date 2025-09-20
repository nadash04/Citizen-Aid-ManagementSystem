# backend_functions.py - Improved and Complete Version

import csv
import os
import datetime
import tempfile
import shutil
import hashlib

# Configuration: Define file paths and Fieldnames
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITIZENS_CSV_FILE = os.path.join(BASE_DIR, "citizens_data.csv")
ADMINS_CSV_FILE = os.path.join(BASE_DIR, "admins_data.csv")
AID_HISTORY_CSV_FILE = os.path.join(BASE_DIR, "aid_history.csv")
MESSAGES_CSV_FILE = os.path.join(BASE_DIR, "messages.csv")
ID_COUNTER_FILE = os.path.join(BASE_DIR, "citizen_id_counter.txt")

# Define the exact headers/fieldnames for CSV files
CITIZENS_FIELDNAMES = [
    "id", "national_id", "full_name", "date_of_birth", "phone_number", 
    "address", "household_members", "dependents", "needs_description", 
    "priority_score", "is_active", "registration_date", "secret_code_hash"
]

ADMINS_FIELDNAMES = [
    "id", "username", "password_hash", "full_name", "organization_id", "role"
]

AID_HISTORY_FIELDNAMES = [
    "id", "citizen_internal_id", "entry_type", "date", "next_date", "timestamp"
]

MESSAGES_FIELDNAMES = [
    "id", "citizen_internal_id", "message", "timestamp"
]

# Helper Functions
def _hash_password(password):
    """Hashes password using SHA-256 with salt."""
    salt = "citizen_aid_system_2024"  # In production, use random salt per user
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def read_csv_dict(file_path, fieldnames):
    """Reads a CSV file and yields each row as a dictionary."""
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {field: row.get(field, "") for field in fieldnames}
    except FileNotFoundError:
        print(f"Info: File not found {file_path}. Returning empty data.")
        return
    except Exception as e:
        print(f"Error reading CSV {file_path}: {e}")
        return

def append_csv_dict(file_path, data_dict, fieldnames):
    """Appends a single dictionary as a new row to a CSV file."""
    file_exists = os.path.isfile(file_path) and os.path.getsize(file_path) > 0
    try:
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            row_to_write = {field: data_dict.get(field, "") for field in fieldnames}
            writer.writerow(row_to_write)
        return True
    except IOError as e:
        print(f"Error appending to CSV {file_path}: {e}")
        return False

def overwrite_csv_dict(file_path, list_of_dicts, fieldnames):
    """Overwrites a CSV file with a list of dictionaries."""
    temp_file_path = None
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        temp_fd, temp_file_path = tempfile.mkstemp(dir=os.path.dirname(file_path) or ".", prefix=os.path.basename(file_path) + ".tmp")
        with os.fdopen(temp_fd, "w", newline="", encoding="utf-8") as temp_f:
            writer = csv.DictWriter(temp_f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
            writer.writeheader()
            rows_to_write = []
            for data_dict in list_of_dicts:
                rows_to_write.append({field: data_dict.get(field, "") for field in fieldnames})
            writer.writerows(rows_to_write)
        
        shutil.move(temp_file_path, file_path)
        return True
    except Exception as e:
        print(f"Error overwriting CSV {file_path}: {e}")
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass
        return False

def get_next_citizen_id_csv():
    """Determines the next citizen ID by finding the max ID in the CSV file."""
    max_id = 0
    try:
        existing_ids = []
        for citizen in read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES):
            try:
                citizen_id = int(citizen.get("id", 0))
                existing_ids.append(citizen_id)
            except (ValueError, TypeError):
                print(f"Warning: Skipping row with invalid ID format: {citizen.get('id')}")
                continue

        if existing_ids:
            max_id = max(existing_ids)
        else:
            try:
                if os.path.exists(ID_COUNTER_FILE):
                    with open(ID_COUNTER_FILE, "r") as f:
                        content = f.read().strip()
                        if content:
                            counter_val = int(content)
                            if counter_val > max_id: 
                                max_id = counter_val - 1
            except (IOError, ValueError):
                max_id = 0

    except FileNotFoundError:
        max_id = 0
    except Exception as e:
        print(f"Error reading {CITIZENS_CSV_FILE} to determine max ID: {e}. Starting ID from 0.")
        max_id = 0

    next_id = max_id + 1

    try:
        os.makedirs(os.path.dirname(ID_COUNTER_FILE) or ".", exist_ok=True)
        with open(ID_COUNTER_FILE, "w") as f:
            f.write(str(next_id))
    except IOError as e:
        print(f"Warning: Could not update {ID_COUNTER_FILE}: {e}")

    return next_id

def get_next_id_for_table(csv_file, fieldnames):
    """Generic function to get next ID for any table."""
    max_id = 0
    try:
        for row in read_csv_dict(csv_file, fieldnames):
            try:
                row_id = int(row.get("id", 0))
                if row_id > max_id:
                    max_id = row_id
            except (ValueError, TypeError):
                continue
    except Exception:
        pass
    return max_id + 1

def setup_csv_files():
    """Creates data files if they don't exist."""
    files_to_setup = {
        CITIZENS_CSV_FILE: CITIZENS_FIELDNAMES,
        ADMINS_CSV_FILE: ADMINS_FIELDNAMES,
        AID_HISTORY_CSV_FILE: AID_HISTORY_FIELDNAMES,
        MESSAGES_CSV_FILE: MESSAGES_FIELDNAMES
    }
    
    for file_path, fieldnames in files_to_setup.items():
        if not os.path.isfile(file_path):
            try:
                os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                print(f"Created {file_path} with headers: {fieldnames}")
            except IOError as e:
                print(f"Error creating {file_path}: {e}")
                
    if not os.path.exists(ID_COUNTER_FILE):
        try:
            with open(ID_COUNTER_FILE, "w") as f:
                f.write("0")
            print(f"Created and initialized {ID_COUNTER_FILE}")
        except IOError as e:
            print(f"Error creating {ID_COUNTER_FILE}: {e}")
             
    print("CSV File setup check complete.")

# Authentication Module Operations
def verify_admin_login_csv(username, password):
    """Checks admin credentials by reading the admins CSV file."""
    password_hash = _hash_password(password)
    for admin in read_csv_dict(ADMINS_CSV_FILE, ADMINS_FIELDNAMES):
        if admin.get("username") == username and admin.get("password_hash") == password_hash:
            return admin
    return None

def verify_citizen_login_csv(national_id, secret_code):
    """Checks citizen credentials using national_id and secret_code."""
    provided_hash = _hash_password(secret_code)
    for citizen in read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES):
        is_active_str = citizen.get("is_active", "True")
        is_active = is_active_str.strip().lower() == "true"
        stored_hash = citizen.get("secret_code_hash", "")
        
        if (citizen.get("national_id") == national_id and 
            stored_hash == provided_hash and
            is_active):
            try:
                citizen["id"] = int(citizen["id"])
                citizen["priority_score"] = float(citizen.get("priority_score", 0.0))
                citizen["household_members"] = int(citizen.get("household_members", 0))
                citizen["dependents"] = int(citizen.get("dependents", 0))
                citizen["is_active"] = True
                if "secret_code_hash" in citizen: 
                    del citizen["secret_code_hash"]
            except (ValueError, TypeError):
                print(f"Warning: Conversion error during login check for citizen ID {citizen.get('id')}")
            return citizen
    return None

# Citizen Registration Module Operations
def check_citizen_exists_csv(national_id):
    """Checks if a citizen with the given National ID already exists."""
    for citizen in read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES):
        if citizen.get("national_id") == national_id:
            return True
    return False

def register_citizen_csv(citizen_data):
    """Registers a new citizen by appending to the citizens CSV file."""
    if "national_id" not in citizen_data or "secret_code" not in citizen_data or "full_name" not in citizen_data:
        print("Error: Registration requires at least national_id, full_name, and secret_code.")
        return None
        
    if check_citizen_exists_csv(citizen_data["national_id"]):
        print(f"Error: Citizen with National ID {citizen_data['national_id']} already exists.")
        return None

    new_id = get_next_citizen_id_csv()
    if new_id is None:
        print("Critical Error: Could not generate a unique citizen ID.")
        return None

    secret_hash = _hash_password(citizen_data["secret_code"])

    new_record = {
        "id": str(new_id),
        "national_id": citizen_data["national_id"],
        "full_name": citizen_data["full_name"],
        "date_of_birth": citizen_data.get("date_of_birth", ""),
        "phone_number": citizen_data.get("phone_number", ""),
        "address": citizen_data.get("address", ""),
        "household_members": str(citizen_data.get("household_members", 0)),
        "dependents": str(citizen_data.get("dependents", 0)),
        "needs_description": citizen_data.get("needs_description", ""),
        "priority_score": str(citizen_data.get("priority_score", 0.0)),
        "is_active": "True",
        "registration_date": datetime.datetime.now().isoformat(),
        "secret_code_hash": secret_hash
    }

    if append_csv_dict(CITIZENS_CSV_FILE, new_record, CITIZENS_FIELDNAMES):
        print(f"Successfully registered citizen with ID: {new_id}")
        del new_record["secret_code_hash"]
        return new_record
    else:
        print("Error: Failed to append citizen data to CSV file.")
        return None

def register_admin_csv(username, password, full_name="", organization_id="", role="admin"):
    """Registers a new admin by appending to the admins CSV file."""
    # Check if admin already exists
    for admin in read_csv_dict(ADMINS_CSV_FILE, ADMINS_FIELDNAMES):
        if admin.get("username") == username:
            print(f"Error: Admin with username {username} already exists.")
            return False

    new_id = get_next_id_for_table(ADMINS_CSV_FILE, ADMINS_FIELDNAMES)
    password_hash = _hash_password(password)

    new_admin = {
        "id": str(new_id),
        
        "username": username,
        "password_hash": password_hash,
        "full_name": full_name,
        "organization_id": organization_id,
        "role": role
    }

    if append_csv_dict(ADMINS_CSV_FILE, new_admin, ADMINS_FIELDNAMES):
        print(f"Successfully registered admin with ID: {new_id}")
        return True
    else:
        print("Error: Failed to append admin data to CSV file.")
        return False

def update_citizen_details_csv(citizen_id, updated_data):
    """Updates a citizen's record by rewriting the entire CSV file.
       Uses internal ID (auto-incremented).
       Handles data type conversion back to string for storage.
    """
    print(f"CSV file path: {CITIZENS_CSV_FILE}") 
    all_citizens_dicts = list(read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES)) # Read all into memory
    updated = False
    citizen_found = False
    str_citizen_id = str(citizen_id)

    for i, citizen_dict in enumerate(all_citizens_dicts):
        if citizen_dict.get("id") == str_citizen_id:
            citizen_found = True
            # Check for National ID uniqueness if it's being updated
            if "national_id" in updated_data and updated_data["national_id"] != citizen_dict.get("national_id"):
                new_nat_id = updated_data["national_id"]
                for other_citizen in all_citizens_dicts:
                    # Ensure we don't compare the citizen to itself
                    if other_citizen.get("id") != str_citizen_id and other_citizen.get("national_id") == new_nat_id:
                        print(f"Error: New National ID {new_nat_id} already exists for another citizen (ID: {other_citizen.get('id')}).")
                        return False # Prevent update
            
            # Update the dictionary - convert values back to string where necessary
            for key, value in updated_data.items():
                if key in CITIZENS_FIELDNAMES:
                    # Convert numbers/booleans back to string for CSV storage
                    if isinstance(value, (int, float)):
                        all_citizens_dicts[i][key] = str(value)
                    elif isinstance(value, bool):
                        all_citizens_dicts[i][key] = str(value)
                    elif value is None: # Handle None values if necessary
                         all_citizens_dicts[i][key] = "" # Store as empty string
                    else:
                        all_citizens_dicts[i][key] = str(value) # Convert others to string just in case
            updated = True
            # Note: Score recalculation based on updated fields might be needed here.
            break # Found and updated

    if not citizen_found:
        print(f"Error: Citizen with ID {citizen_id} not found for update.")
        return False
        
    if not updated:
         print(f"No valid changes applied for citizen {citizen_id}.")
         return True # No changes needed, considered success

    # Rewrite the entire file
    if overwrite_csv_dict(CITIZENS_CSV_FILE, all_citizens_dicts, CITIZENS_FIELDNAMES):
        print(f"Successfully updated details for citizen {citizen_id} by rewriting CSV.")
        return True
    else:
        print(f"Error: Failed to rewrite {CITIZENS_CSV_FILE} during update.")
        return False

# --- Keep existing .txt file operations for aid_history and messages ---
# These were not part of the original csv_based_operations_examples.py
# and require separate handling if they need to be moved to CSV.

def save_aid_history_entry(citizen_internal_id, entry_type, date_str, next_date_str):
    """Appends an entry to aid_history.txt using the internal citizen ID."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname("aid_history.txt") or ".", exist_ok=True)
        with open("aid_history.txt", "a", encoding="utf-8") as f:
            f.write(f"{citizen_internal_id},{entry_type},{date_str},{next_date_str}\n")
        return True
    except IOError as e:
        print(f"Error writing to aid_history.txt: {e}")
        return False

def save_message_entry(citizen_internal_id, message):
    """Appends a message to messages.txt using the internal citizen ID."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname("messages.txt") or ".", exist_ok=True)
        with open("messages.txt", "a", encoding="utf-8") as f:
            f.write(f"{citizen_internal_id},{message}\n")
        return True
    except IOError as e:
        print(f"Error writing to messages.txt: {e}")
        return False
# Dashboard Operations
def get_citizens_list_csv(sort_by="priority_score", filter_criteria=None, include_inactive=False):
    """Reads the entire citizens CSV, filters/sorts in memory."""
    all_citizens = []
    for row in read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES):
        if "secret_code_hash" in row: 
            del row["secret_code_hash"]
        
        try:
            row["id"] = int(row.get("id", 0))
            row["priority_score"] = float(row.get("priority_score", 0.0))
            row["household_members"] = int(row.get("household_members", 0))
            row["dependents"] = int(row.get("dependents", 0))
            is_active_str = row.get("is_active", "True")
            row["is_active"] = is_active_str.strip().lower() == "true"
        except (ValueError, TypeError):
            print(f"Warning: Data conversion error for citizen ID {row.get('id')}")
            continue

        if not include_inactive and not row["is_active"]:
            continue

        if filter_criteria:
            # Apply custom filter logic here if needed
            pass

        all_citizens.append(row)

    # Sort the list
    if sort_by == "priority_score":
        all_citizens.sort(key=lambda x: x.get("priority_score", 0.0), reverse=True)
    elif sort_by == "id":
        all_citizens.sort(key=lambda x: x.get("id", 0))
    elif sort_by == "full_name":
        all_citizens.sort(key=lambda x: x.get("full_name", ""))

    return all_citizens

def get_citizen_details_csv(citizen_internal_id):
    """Retrieves detailed information for a specific citizen by internal ID."""
    try:
        citizen_internal_id = int(citizen_internal_id)
    except (ValueError, TypeError):
        print(f"Error: Invalid citizen internal ID format: {citizen_internal_id}")
        return None

    for citizen in read_csv_dict(CITIZENS_CSV_FILE, CITIZENS_FIELDNAMES):
        try:
            if int(citizen.get("id", 0)) == citizen_internal_id:
                if "secret_code_hash" in citizen:
                    del citizen["secret_code_hash"]
                
                citizen["id"] = int(citizen["id"])
                citizen["priority_score"] = float(citizen.get("priority_score", 0.0))
                citizen["household_members"] = int(citizen.get("household_members", 0))
                citizen["dependents"] = int(citizen.get("dependents", 0))
                is_active_str = citizen.get("is_active", "True")
                citizen["is_active"] = is_active_str.strip().lower() == "true"
                
                return citizen
        except (ValueError, TypeError):
            continue
    
    print(f"Warning: Citizen with internal ID {citizen_internal_id} not found.")
    return None

# Aid History Operations
def save_aid_history_entry(citizen_internal_id, entry_type, date_str, next_date_str=""):
    """Saves an aid history entry to the CSV file."""
    new_id = get_next_id_for_table(AID_HISTORY_CSV_FILE, AID_HISTORY_FIELDNAMES)
    
    entry = {
        "id": str(new_id),
        "citizen_internal_id": str(citizen_internal_id),
        "entry_type": entry_type,
        "date": date_str,
        "next_date": next_date_str,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return append_csv_dict(AID_HISTORY_CSV_FILE, entry, AID_HISTORY_FIELDNAMES)

def read_aid_history(citizen_internal_id=None):
    """Reads aid history entries, optionally filtered by citizen ID."""
    history = []
    for entry in read_csv_dict(AID_HISTORY_CSV_FILE, AID_HISTORY_FIELDNAMES):
        if citizen_internal_id is None or entry.get("citizen_internal_id") == str(citizen_internal_id):
            history.append(entry)
    return history

def check_citizen_received_aid(citizen_internal_id):
    """Checks if a citizen has received aid (has entry with empty next_date)."""
    for entry in read_csv_dict(AID_HISTORY_CSV_FILE, AID_HISTORY_FIELDNAMES):
        if (entry.get("citizen_internal_id") == str(citizen_internal_id) and 
            entry.get("next_date", "").strip() == ""):
            return True
    return False

# Messages Operations
def save_message_entry(citizen_internal_id, message):
    """Saves a message entry to the CSV file."""
    new_id = get_next_id_for_table(MESSAGES_CSV_FILE, MESSAGES_FIELDNAMES)
    
    entry = {
        "id": str(new_id),
        "citizen_internal_id": str(citizen_internal_id),
        "message": message,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return append_csv_dict(MESSAGES_CSV_FILE, entry, MESSAGES_FIELDNAMES)

def read_messages(citizen_internal_id=None):
    """Reads message entries, optionally filtered by citizen ID."""
    messages = []
    for entry in read_csv_dict(MESSAGES_CSV_FILE, MESSAGES_FIELDNAMES):
        if citizen_internal_id is None or entry.get("citizen_internal_id") == str(citizen_internal_id):
            messages.append(entry)
    return messages

# Initialize system on import
if __name__ == "__main__":
    setup_csv_files()
    print("Backend functions module loaded successfully.")

