# integrated_app.py - Complete and Improved Version

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import backend_functions as be
import openpyxl
from tkinter import filedialog

# Global variable to store the internal ID of the currently logged-in citizen
current_user_internal_id = None

# ============================ HELPER FUNCTIONS ============================

def calculate_score(q1_var, q2_var, q3_var, q4_var):
    """Calculates priority score based on registration questions."""
    score = 0
    score += 3 if q1_var.get() == "Yes" else 0
    score += 2 if q2_var.get() == "Yes" else 0
    score += 1 if q3_var.get() == "Yes" else 0
    score += 1 if q4_var.get() == "Yes" else 0
    return float(score)

# ============================ ADMIN SCREENS ============================

def open_add_admin_screen():
    win = tk.Toplevel()
    win.title("Add New Admin")
    win.geometry("400x350")
    tk.Label(win, text="Add New Admin", font=("Helvetica", 16, "bold")).pack(pady=10)
    
    tk.Label(win, text="Username:").pack()
    username_entry = tk.Entry(win, width=30)
    username_entry.pack(pady=5)
    
    tk.Label(win, text="Password:").pack()
    password_entry = tk.Entry(win, show="*", width=30)
    password_entry.pack(pady=5)
    
    tk.Label(win, text="Full Name (Optional):").pack()
    fullname_entry = tk.Entry(win, width=30)
    fullname_entry.pack(pady=5)
    
    tk.Label(win, text="Organization ID (Optional):").pack()
    org_entry = tk.Entry(win, width=30)
    org_entry.pack(pady=5)

    def save_admin():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        fullname = fullname_entry.get().strip()
        org_id = org_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and Password are required.", parent=win)
            return
        
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters long.", parent=win)
            return
        
        success = be.register_admin_csv(username, password, fullname, org_id)
        
        if success:
            messagebox.showinfo("Success", "Admin added successfully!", parent=win)
            open_admin_panel()
            win.destroy()
        else:
            messagebox.showerror("Error", "Failed to add admin. Username might already exist.", parent=win)

    tk.Button(win, text="Save Admin", command=save_admin, bg="#4CAF50", fg="white", 
              font=("Helvetica", 10, "bold")).pack(pady=20)

def open_edit_citizen_screen():
    win = tk.Toplevel()
    win.title("Edit Citizen Info / Add Aid Record")
    win.geometry("500x600")

    tk.Label(win, text="Search Citizen by National ID (9 digits)",
             font=("Helvetica", 14, "bold")).pack(pady=10)

    search_entry = tk.Entry(win, width=20, font=("Helvetica", 12))
    search_entry.pack(pady=5)

    result_label = tk.Label(win, text="", wraplength=450, justify="left")
    result_label.pack(pady=10)

    # Frame for editing details (initially hidden)
    edit_frame = tk.Frame(win, relief="groove", bd=2)

    tk.Label(edit_frame, text="New Aid Date (yyyy-mm-dd, leave blank if received):",
             font=("Helvetica", 10)).pack(pady=5)
    next_date_entry = tk.Entry(edit_frame, width=30)
    next_date_entry.pack(pady=5)

    tk.Label(edit_frame, text="Send Message:", font=("Helvetica", 10)).pack(pady=5)
    message_text = tk.Text(edit_frame, width=40, height=4)
    message_text.pack(pady=5)

    tk.Label(edit_frame, text="Edit Priority Score:", font=("Helvetica", 10)).pack(pady=5)
    score_entry = tk.Entry(edit_frame, width=10)
    score_entry.pack(pady=5)

    found_citizen_internal_id = None
    found_citizen = None

    def search_citizen():
        nonlocal found_citizen_internal_id, found_citizen
        national_id_search = search_entry.get().strip()
        if not national_id_search.isdigit() or len(national_id_search) != 9:
            result_label.config(text="Invalid National ID format (must be 9 digits).", fg="red")
            edit_frame.pack_forget()
            return

        try:
            for citizen in be.read_csv_dict(be.CITIZENS_CSV_FILE, be.CITIZENS_FIELDNAMES):
                if citizen.get("national_id") == national_id_search:
                    is_active = citizen.get("is_active", "True").strip().lower() == "true"
                    if is_active:
                        found_citizen = citizen
                        break
            else:
                found_citizen = None

            if found_citizen:
                found_citizen_internal_id = found_citizen.get("id")
                result_text = f"Found: {found_citizen.get('full_name')} (ID: {found_citizen_internal_id})\n"
                result_text += f"Phone: {found_citizen.get('phone_number')}\n"
                result_text += f"Priority Score: {found_citizen.get('priority_score', 0.0)}"
                result_label.config(text=result_text, fg="green")

                score_entry.delete(0, tk.END)
                score_entry.insert(0, found_citizen.get("priority_score", "0"))
                message_text.delete("1.0", tk.END)
                next_date_entry.delete(0, tk.END)

                edit_frame.pack(pady=10, padx=20, fill="x")
            else:
                result_label.config(text="Citizen not found or is inactive.", fg="red")
                edit_frame.pack_forget()
                found_citizen_internal_id = None

        except Exception as e:
            result_label.config(text=f"Error reading data: {e}", fg="red")
            edit_frame.pack_forget()

    def save_changes():
        if not found_citizen_internal_id:
            messagebox.showerror("Error", "No citizen selected.", parent=win)
            return

        message = message_text.get("1.0", tk.END).strip()
        next_date = next_date_entry.get().strip()
        new_score = score_entry.get().strip()

        if not message and not next_date and not new_score:
            messagebox.showwarning("No Changes", "No changes provided to update.", parent=win)
            return

        success_flags = []

        if next_date:
            try:
                datetime.datetime.strptime(next_date, "%Y-%m-%d")
                aid_success = be.save_aid_history_entry(
                    citizen_internal_id=found_citizen_internal_id,
                    entry_type="AdminEntry",
                    date_str=datetime.datetime.now().strftime("%Y-%m-%d"),
                    next_date_str=next_date
                )
                success_flags.append(aid_success)
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.", parent=win)
                return

        if message:
            msg_success = be.save_message_entry(
                citizen_internal_id=found_citizen_internal_id,
                message=message
            )
            success_flags.append(msg_success)

        if new_score:
            try:
                score_float = float(new_score)
                updated_data = found_citizen.copy()
                updated_data["priority_score"] = score_float
                score_success = be.update_citizen_details_csv(found_citizen_internal_id, updated_data)
                success_flags.append(score_success)
            except ValueError:
                messagebox.showerror("Error", "Invalid score. Please enter a number.", parent=win)
                return

        if any(success_flags):
            messagebox.showinfo("Success", "Aid record, message, and/or score updated successfully!", parent=win)
            search_citizen()
        else:
            messagebox.showwarning("No Update", "No data was updated. Please check inputs.", parent=win)

    # Place search button after defining the function
    tk.Button(win, text="🔍 Search", command=search_citizen,
              bg="#2196F3", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

    # Place save button after defining the function
    tk.Button(edit_frame, text="💾 Save Changes", command=save_changes,
              bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")).pack(pady=10)

def open_sorted_citizens_screen():
    win = tk.Toplevel()
    win.title("Citizens Ranked by Priority Score")
    win.geometry("800x600")

    tk.Label(win, text="Citizens Sorted by Highest Priority Score", 
             font=("Helvetica", 16, "bold")).pack(pady=10)

    # Create frame for the treeview and scrollbar
    tree_frame = tk.Frame(win)
    tree_frame.pack(expand=True, fill="both", padx=20, pady=10)

    columns = ("internal_id", "national_id", "full_name", "phone_number", "priority_score")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
    
    tree.heading("internal_id", text="Internal ID")
    tree.heading("national_id", text="National ID")
    tree.heading("full_name", text="Name")
    tree.heading("phone_number", text="Phone")
    tree.heading("priority_score", text="Score")
    
    tree.column("internal_id", width=80, anchor="center")
    tree.column("national_id", width=100, anchor="center")
    tree.column("full_name", width=200)
    tree.column("phone_number", width=120)
    tree.column("priority_score", width=80, anchor="e")

    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(expand=True, fill="both")

    try:
        sorted_citizens = be.get_citizens_list_csv(sort_by="priority_score")

        if not sorted_citizens:
            tk.Label(win, text="No active citizens found.", fg="orange", 
                    font=("Helvetica", 12)).pack()
        else:
            for citizen in sorted_citizens:
                tree.insert("", tk.END, values=(
                    citizen.get("id", "N/A"),
                    citizen.get("national_id", "N/A"),
                    citizen.get("full_name", "N/A"),
                    citizen.get("phone_number", "N/A"),
                    f"{citizen.get('priority_score', 0.0):.1f}"
                ))

    except Exception as e:
        tk.Label(win, text=f"Error loading citizen data: {e}", fg="red",
                font=("Helvetica", 12)).pack()

def open_admin_panel():
    win = tk.Toplevel()
    win.title("Admin Dashboard")
    win.geometry("1000x700")

    # Top Menu Bar
    menu_bar = tk.Menu(win)
    win.config(menu=menu_bar)
    
    user_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="User Management", menu=user_menu)
    user_menu.add_command(label="➕ Register New Citizen", command=open_register_screen)
    user_menu.add_command(label="📝 Add Aid Record / Message Citizen", command=open_edit_citizen_screen)
    
    admin_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Admin Actions", menu=admin_menu)
    admin_menu.add_command(label="👤 Add New Admin", command=open_add_admin_screen)
    admin_menu.add_command(label="📊 View Sorted Citizens (by Score)", command=open_sorted_citizens_screen)
    
    menu_bar.add_command(label="🚪 Exit Dashboard", command=win.destroy)

    # Header
    header_frame = tk.Frame(win, bg="#2196F3", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Admin Dashboard", font=("Helvetica", 18, "bold"),
             bg="#2196F3", fg="white").pack(expand=True)

    # Filter Options
    filter_frame = tk.Frame(win)
    filter_frame.pack(pady=10, padx=10, fill="x")
    tk.Label(filter_frame, text="Filter by Aid Status:", 
             font=("Helvetica", 11, "bold")).pack(side="left", padx=5)
    filter_var = tk.StringVar(value="All users")
    filter_options = ["All users", "Received", "Not Received"]
    filter_menu = ttk.Combobox(filter_frame, textvariable=filter_var, values=filter_options, 
                              state="readonly", width=15)
    filter_menu.pack(side="left", padx=5)

    # Citizen Table Frame
    table_frame = tk.Frame(win)
    table_frame.pack(pady=10, padx=10, expand=True, fill="both")

    citizen_columns = ("internal_id", "national_id", "full_name", "phone_number", 
                      "priority_score", "received_aid")
    citizen_tree = ttk.Treeview(table_frame, columns=citizen_columns, show="headings")
    
    citizen_tree.heading("internal_id", text="ID")
    citizen_tree.heading("national_id", text="National ID")
    citizen_tree.heading("full_name", text="Name")
    citizen_tree.heading("phone_number", text="Phone")
    citizen_tree.heading("priority_score", text="Score")
    citizen_tree.heading("received_aid", text="Received Aid?")
    
    citizen_tree.column("internal_id", width=60, anchor="center")
    citizen_tree.column("national_id", width=100, anchor="center")
    citizen_tree.column("full_name", width=200)
    citizen_tree.column("phone_number", width=120)
    citizen_tree.column("priority_score", width=60, anchor="e")
    citizen_tree.column("received_aid", width=100, anchor="center")
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=citizen_tree.yview)
    citizen_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    citizen_tree.pack(expand=True, fill="both")

    def load_citizen_data(filter_status="All users"):
        for item in citizen_tree.get_children():
            citizen_tree.delete(item)
            
        try:
            all_citizens = be.get_citizens_list_csv(sort_by="id")
            
            if not all_citizens:
                citizen_tree.insert("", tk.END, values=("", "", "No active citizens found.", "", "", ""))
                return

            for citizen in all_citizens:
                citizen_internal_id = citizen.get("id")
                received_status = "Yes" if be.check_citizen_received_aid(citizen_internal_id) else "No"
                
                if (filter_status == "All users" or 
                   (filter_status == "Received" and received_status == "Yes") or 
                   (filter_status == "Not Received" and received_status == "No")):
                    
                    citizen_tree.insert("", tk.END, values=(
                        citizen_internal_id,
                        citizen.get("national_id", "N/A"),
                        citizen.get("full_name", "N/A"),
                        citizen.get("phone_number", "N/A"),
                        f"{citizen.get('priority_score', 0.0):.1f}",
                        received_status
                    ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load citizen data: {e}", parent=win)
            citizen_tree.insert("", tk.END, values=("", "", f"Error: {e}", "", "", ""))

    load_citizen_data()

    def on_filter_change(event):
        load_citizen_data(filter_var.get())
    filter_menu.bind("<<ComboboxSelected>>", on_filter_change)

    # Statistics Frame
    stats_frame = tk.Frame(win, relief="groove", bd=2)
    stats_frame.pack(pady=10, padx=10, fill="x")
    tk.Label(stats_frame, text="📊 System Statistics", 
             font=("Arial", 14, "bold")).pack(pady=5)

    stats_columns = ("Total Citizens", "Received Aid", "Not Received", "Aid Operations")
    stats_tree = ttk.Treeview(stats_frame, columns=stats_columns, show="headings", height=1)
    
    for col in stats_columns:
        stats_tree.heading(col, text=col)
        stats_tree.column(col, width=150, anchor="center")
    stats_tree.pack(pady=5)

    def update_stats():
        for item in stats_tree.get_children():
            stats_tree.delete(item)
            
        try:
            all_citizens = list(be.read_csv_dict(be.CITIZENS_CSV_FILE, be.CITIZENS_FIELDNAMES))
            total_citizens = len(all_citizens)
            
            aid_history = be.read_aid_history()
            total_aid_ops = len(aid_history)
            
            received_ids = set()
            for citizen in all_citizens:
                internal_id = citizen.get("id")
                if internal_id and be.check_citizen_received_aid(internal_id):
                    received_ids.add(internal_id)
            received_count = len(received_ids)
            
            not_received = total_citizens - received_count 
            
            stats_tree.insert("", tk.END, values=(total_citizens, received_count, 
                                                 not_received, total_aid_ops))
            
        except Exception as e:
            stats_tree.insert("", tk.END, values=(f"Error: {e}", "", "", ""))

    update_stats()
    tk.Button(stats_frame, text="Refresh Stats", command=update_stats,
              bg="#FF9800", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)
    
    def extract_to_excel():
        try:
            # Ask user where to save the Excel file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                title="Save Excel File"
            )

            if not file_path:
                return  # User cancelled the save dialog

            # Load citizen data from backend
            citizens = be.get_citizens_list_csv(sort_by="id")

            # Create a new Excel workbook and worksheet
            workbook = openpyxl.Workbook()
            worksheet = workbook.active
            worksheet.title = "Citizens Data"

            # Define table headers
            headers = ["ID", "National ID", "Full Name", "Phone Number", "Priority Score", "Received Aid"]
            worksheet.append(headers)

            # Add each citizen's data as a row
            for citizen in citizens:
                citizen_id = citizen.get("id", "")
                received_aid = "Yes" if be.check_citizen_received_aid(citizen_id) else "No"

                row = [
                    citizen_id,
                    citizen.get("national_id", ""),
                    citizen.get("full_name", ""),
                    citizen.get("phone_number", ""),
                    f"{citizen.get('priority_score', 0.0):.1f}",
                    received_aid
                ]
                worksheet.append(row)

            # Save workbook to selected file path
            workbook.save(file_path)

            messagebox.showinfo(
                "Success",
                f"Data exported successfully to:\n{file_path}",
                parent=win
            )

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export data:\n{e}",
                parent=win
            )

    
    tk.Button(stats_frame, text="Extract Data", command=extract_to_excel,
          bg="#FF9800", fg="white", font=("Helvetica", 10, "bold")).pack(pady=5)

# ========================== CITIZEN SYSTEM ==============================

def open_register_screen():
    register_win = tk.Toplevel()
    register_win.title("Citizen Registration")
    register_win.geometry("500x700")
    
    # Header
    header_frame = tk.Frame(register_win, bg="#4CAF50", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Register New Citizen", font=("Helvetica", 18, "bold"),
             bg="#4CAF50", fg="white").pack(expand=True)

    # Main form frame
    form_frame = tk.Frame(register_win)
    form_frame.pack(pady=20, padx=20, fill="both", expand=True)

    tk.Label(form_frame, text="Full Name:", font=("Helvetica", 11, "bold")).pack(anchor="w")
    name_entry = tk.Entry(form_frame, width=40, font=("Helvetica", 11))
    name_entry.pack(pady=(0, 10), fill="x")
    
    tk.Label(form_frame, text="National ID Number (9 digits):", 
             font=("Helvetica", 11, "bold")).pack(anchor="w")
    national_id_entry = tk.Entry(form_frame, width=40, font=("Helvetica", 11))
    national_id_entry.pack(pady=(0, 10), fill="x")
    
    tk.Label(form_frame, text="Phone Number (10 digits):", 
             font=("Helvetica", 11, "bold")).pack(anchor="w")
    phone_entry = tk.Entry(form_frame, width=40, font=("Helvetica", 11))
    phone_entry.pack(pady=(0, 10), fill="x")
    
    tk.Label(form_frame, text="Secret Code (for login):", 
             font=("Helvetica", 11, "bold")).pack(anchor="w")
    secret_entry = tk.Entry(form_frame, show="*", width=40, font=("Helvetica", 11))
    secret_entry.pack(pady=(0, 20), fill="x")

    def create_yes_no_question(parent, text):
        var = tk.StringVar(value="No")
        frame = tk.Frame(parent)
        tk.Label(frame, text=text, font=("Helvetica", 10)).pack(side="left", padx=5)
        ttk.Radiobutton(frame, text="Yes", variable=var, value="Yes").pack(side="left", padx=5)
        ttk.Radiobutton(frame, text="No", variable=var, value="No").pack(side="left", padx=5)
        frame.pack(anchor="w", pady=5, fill="x")
        return var

    tk.Label(form_frame, text="Answer the following for Priority Score:", 
             font=("Helvetica", 12, "bold")).pack(pady=(10, 5), anchor="w")
    
    q1 = create_yes_no_question(form_frame, "Breadwinner has disabilities?")
    q2 = create_yes_no_question(form_frame, "Children have disabilities?")
    q3 = create_yes_no_question(form_frame, "Fixed income?")
    q4 = create_yes_no_question(form_frame, "More than 4 family members?")

    def register():
        name = name_entry.get().strip()
        national_id = national_id_entry.get().strip()
        phone = phone_entry.get().strip()
        secret_code = secret_entry.get().strip()

        if not name or not national_id or not phone or not secret_code:
            messagebox.showerror("Error", "All fields are required.", parent=register_win)
            return
            
        if not national_id.isdigit() or len(national_id) != 9:
            messagebox.showerror("Error", "National ID must be exactly 9 digits.", parent=register_win)
            return
            
        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Error", "Phone number must be exactly 10 digits.", parent=register_win)
            return
            
        if len(secret_code) < 4:
            messagebox.showerror("Error", "Secret code must be at least 4 characters long.", parent=register_win)
            return

        if be.check_citizen_exists_csv(national_id):
            messagebox.showerror("Error", f"A citizen with National ID {national_id} already exists.", 
                                parent=register_win)
            return

        score = calculate_score(q1, q2, q3, q4)

        citizen_data = {
            "national_id": national_id,
            "full_name": name,
            "phone_number": phone,
            "secret_code": secret_code,
            "priority_score": score,
            "date_of_birth": "", 
            "address": "", 
            "household_members": 0, 
            "dependents": 0, 
            "needs_description": ""
        }

        registered_record = be.register_citizen_csv(citizen_data)

        if registered_record:
            new_internal_id = registered_record.get("id")
            messagebox.showinfo("Success", 
                              f"Registration successful!\nYour Internal System ID: {new_internal_id}\n"
                              f"Please keep this ID and your secret code for login.", 
                              parent=register_win)
            open_citizen_login()
            register_win.destroy()
        else:
            messagebox.showerror("Error", "Registration failed. Please try again.", parent=register_win)

    tk.Button(form_frame, text="Register", font=("Helvetica", 12, "bold"), 
              command=register, bg="#4CAF50", fg="white", height=2).pack(pady=20, fill="x")

def open_citizen_login():
    login_win = tk.Toplevel()
    login_win.title("Citizen Login")
    login_win.geometry("450x400")
    
    # Header
    header_frame = tk.Frame(login_win, bg="#2196F3", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Citizen Login", font=("Helvetica", 18, "bold"),
             bg="#2196F3", fg="white").pack(expand=True)

    # Form frame
    form_frame = tk.Frame(login_win)
    form_frame.pack(pady=30, padx=30, fill="both", expand=True)

    tk.Label(form_frame, text="National ID (9 digits):", 
             font=("Helvetica", 11, "bold")).pack(anchor="w")
    national_id_entry = tk.Entry(form_frame, width=30, font=("Helvetica", 12))
    national_id_entry.pack(pady=(0, 15), fill="x")
    
    tk.Label(form_frame, text="Secret Code:", font=("Helvetica", 11, "bold")).pack(anchor="w")
    secret_entry = tk.Entry(form_frame, show="*", width=30, font=("Helvetica", 12))
    secret_entry.pack(pady=(0, 20), fill="x")

    def login_check():
        global current_user_internal_id
        national_id = national_id_entry.get().strip()
        secret_code = secret_entry.get().strip()
        
        if not national_id or not secret_code:
            messagebox.showerror("Error", "National ID and Secret Code are required.", parent=login_win)
            return
            
        if not national_id.isdigit() or len(national_id) != 9:
            messagebox.showerror("Error", "National ID must be exactly 9 digits.", parent=login_win)
            return

        try:
            citizen_record = be.verify_citizen_login_csv(national_id, secret_code)
            
            if citizen_record:
                current_user_internal_id = citizen_record.get("id")
                messagebox.showinfo("Success", f"Login successful! Welcome {citizen_record.get('full_name')}.", 
                                  parent=login_win)
                login_win.destroy()
                open_citizen_dashboard()
            else:
                messagebox.showerror("Error", "Login failed. Invalid credentials or inactive account.", 
                                   parent=login_win)
                current_user_internal_id = None
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during login: {e}", parent=login_win)
            current_user_internal_id = None

    tk.Button(form_frame, text="Login", command=login_check, bg="#2196F3", fg="white",
              font=("Helvetica", 12, "bold"), height=2).pack(pady=10, fill="x")
    
    tk.Label(form_frame, text="Don't have an account?", font=("Helvetica", 10)).pack(pady=(20, 5))
    tk.Button(form_frame, text="Register here", fg="blue", relief="flat", 
              command=lambda: [login_win.destroy(), open_register_screen()], font=("Helvetica", 10, "underline")).pack()

def open_edit_info_screen():
    edit_win = tk.Toplevel()
    edit_win.title("Citizen Edit Information")
    edit_win.geometry("500x700")

    # Header
    header_frame = tk.Frame(edit_win, bg="#4CAF50", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Edit Your Info", font=("Helvetica", 18, "bold"),
             bg="#4CAF50", fg="white").pack(expand=True)

    form_frame = tk.Frame(edit_win)
    form_frame.pack(pady=20, padx=20, fill="both", expand=True)

    citizen_details = be.get_citizen_details_csv(current_user_internal_id)
    
    if not citizen_details:
        messagebox.showerror("Error", "Could not retrieve citizen details.", parent=edit_win)
        edit_win.destroy()
        return

    # Full Name
    tk.Label(form_frame, text="Full Name:", font=("Helvetica", 11, "bold")).pack(anchor="w")
    name_entry = tk.Entry(form_frame, font=("Helvetica", 11))
    name_entry.pack(fill="x", pady=(0, 10))
    name_entry.insert(0, citizen_details.get('full_name', ''))

    # National ID
    tk.Label(form_frame, text="National ID Number (9 digits):", font=("Helvetica", 11, "bold")).pack(anchor="w")
    national_id_entry = tk.Entry(form_frame, font=("Helvetica", 11))
    national_id_entry.pack(fill="x", pady=(0, 10))
    national_id_entry.insert(0, citizen_details.get('national_id', ''))

    # Phone
    tk.Label(form_frame, text="Phone Number (10 digits):", font=("Helvetica", 11, "bold")).pack(anchor="w")
    phone_entry = tk.Entry(form_frame, font=("Helvetica", 11))
    phone_entry.pack(fill="x", pady=(0, 10))
    phone_entry.insert(0, citizen_details.get('phone_number', ''))

    # Priority Questions
    def create_yes_no_question(parent, text):
        var = tk.StringVar(value="No")
        frame = tk.Frame(parent)
        tk.Label(frame, text=text, font=("Helvetica", 10)).pack(side="left", padx=5)
        ttk.Radiobutton(frame, text="Yes", variable=var, value="Yes").pack(side="left", padx=5)
        ttk.Radiobutton(frame, text="No", variable=var, value="No").pack(side="left", padx=5)
        frame.pack(anchor="w", pady=5, fill="x")
        return var

    tk.Label(form_frame, text="Answer the following for Priority Score:", font=("Helvetica", 12, "bold")).pack(pady=(10, 5), anchor="w")
    q1 = create_yes_no_question(form_frame, "Breadwinner has disabilities?")
    q2 = create_yes_no_question(form_frame, "Children have disabilities?")
    q3 = create_yes_no_question(form_frame, "No Fixed income?")
    q4 = create_yes_no_question(form_frame, "More than 4 family members?")

    def edit():
        name = name_entry.get().strip()
        national_id = national_id_entry.get().strip()
        phone = phone_entry.get().strip()

        if not name or not national_id or not phone:
            messagebox.showerror("Error", "Full Name, National ID, and Phone Number are required.", parent=edit_win)
            return

        if not national_id.isdigit() or len(national_id) != 9:
            messagebox.showerror("Error", "National ID must be exactly 9 digits.", parent=edit_win)
            return

        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Error", "Phone number must be exactly 10 digits.", parent=edit_win)
            return

        score = calculate_score(q1, q2, q3, q4)

        citizen_data = {
            "national_id": national_id,
            "full_name": name,
            "phone_number": phone,
            "priority_score": score,
            "date_of_birth": "",
            "address": "",
            "household_members": 0,
            "dependents": 0,
            "needs_description": ""
        }

        edited_record = be.update_citizen_details_csv(current_user_internal_id, citizen_data)

        if edited_record:
            edit_win.destroy()
            open_citizen_dashboard()
        else:
            messagebox.showerror("Error", "Editing failed. Could not save data.", parent=edit_win)

    tk.Button(form_frame, text="Save Changes", font=("Helvetica", 12, "bold"), 
              command=edit, bg="#4CAF50", fg="white", height=2).pack(pady=20, fill="x")

def open_citizen_dashboard():
    """Opens the main dashboard for a logged-in citizen."""
    if current_user_internal_id is None:
        messagebox.showerror("Error", "No citizen logged in.")
        return
        
    dashboard = tk.Toplevel()
    dashboard.title("Citizen Dashboard")
    dashboard.geometry("700x600")

    citizen_details = be.get_citizen_details_csv(current_user_internal_id)
    if not citizen_details:
        messagebox.showerror("Error", "Could not retrieve citizen details.", parent=dashboard)
        dashboard.destroy()
        return

    # Header
    header_frame = tk.Frame(dashboard, bg="#4CAF50", height=80)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    welcome_text = f"Welcome, {citizen_details.get('full_name', '')}!"
    tk.Label(header_frame, text=welcome_text, font=("Helvetica", 18, "bold"),
             bg="#4CAF50", fg="white").pack(expand=True)

    # Info frame
    info_frame = tk.Frame(dashboard)
    info_frame.pack(pady=10, padx=20, fill="x")
    
    info_text = f"Internal ID: {current_user_internal_id} | "
    info_text += f"National ID: {citizen_details.get('national_id', '')} | "
    info_text += f"Phone: {citizen_details.get('phone_number', '')} | "
    info_text += f"Priority Score: {citizen_details.get('priority_score', 0.0):.1f}"
    
    tk.Label(info_frame, text=info_text, font=("Helvetica", 10), 
             wraplength=650, justify="center").pack()

    # Main content frame
    content_frame = tk.Frame(dashboard, bd=2, relief="groove")
    content_frame.pack(pady=20, padx=20, fill="both", expand=True)

    tk.Label(content_frame, text="Aid History", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
    aid_text = scrolledtext.ScrolledText(content_frame, height=8, width=70, wrap=tk.WORD,
                                        font=("Helvetica", 10))
    aid_text.pack(pady=5, padx=10, fill="both", expand=True)
    aid_text.config(state="disabled")

    tk.Label(content_frame, text="Messages from Admin", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))
    msg_text = scrolledtext.ScrolledText(content_frame, height=8, width=70, wrap=tk.WORD,
                                        font=("Helvetica", 10))
    msg_text.pack(pady=5, padx=10, fill="both", expand=True)
    msg_text.config(state="disabled")

    def load_info():
        aid_history = be.read_aid_history(current_user_internal_id)
        messages = be.read_messages(current_user_internal_id)
        
        aid_text.config(state="normal")
        aid_text.delete(1.0, tk.END)
        if aid_history:
            for entry in aid_history:
                status = "Received" if entry.get('next_date') == "" else f"Next Aid: {entry.get('next_date', 'TBD')}"
                aid_text.insert(tk.END, f"Date: {entry.get('date', 'N/A')} - Type: {entry.get('entry_type', 'N/A')} - Status: {status}\n")
        else:
            aid_text.insert(tk.END, "No aid history found.\n")
        aid_text.config(state="disabled")
        
        msg_text.config(state="normal")
        msg_text.delete(1.0, tk.END)
        if messages:
            for msg in messages:
                msg_text.insert(tk.END, f"- {msg.get('message', '')}\n")
        else:
            msg_text.insert(tk.END, "No messages found.\n")
        msg_text.config(state="disabled")

    load_info()
    
    # Button frame
    button_frame = tk.Frame(dashboard)
    button_frame.pack(pady=10)
    
    tk.Button(button_frame, text="Refresh Info", command=load_info, bg="#FF9800", fg="white",
              font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
    tk.Button(button_frame, text="Update Info", command=lambda: open_edit_info_screen(), bg="#FF9800", fg="white",
              font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
    tk.Button(button_frame, text="Logout", command=lambda: logout(dashboard), bg="#f44336", fg="white",
              font=("Helvetica", 10, "bold")).pack(side="left", padx=5)

def logout(window_to_close):
    global current_user_internal_id
    current_user_internal_id = None
    window_to_close.destroy()
    messagebox.showinfo("Logged Out", "You have been logged out successfully.")

# ========================== ADMIN LOGIN ==============================

def open_admin_login():
    login_win = tk.Toplevel()
    login_win.title("Admin Login")
    login_win.geometry("400x300")
    
    # Header
    header_frame = tk.Frame(login_win, bg="#FF5722", height=60)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Admin Login", font=("Helvetica", 18, "bold"),
             bg="#FF5722", fg="white").pack(expand=True)

    # Form frame
    form_frame = tk.Frame(login_win)
    form_frame.pack(pady=30, padx=30, fill="both", expand=True)

    tk.Label(form_frame, text="Username:", font=("Helvetica", 11, "bold")).pack(anchor="w")
    username_entry = tk.Entry(form_frame, width=30, font=("Helvetica", 12))
    username_entry.pack(pady=(0, 15), fill="x")
    
    tk.Label(form_frame, text="Password:", font=("Helvetica", 11, "bold")).pack(anchor="w")
    password_entry = tk.Entry(form_frame, show="*", width=30, font=("Helvetica", 12))
    password_entry.pack(pady=(0, 20), fill="x")

    def admin_login_check():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and Password are required.", parent=login_win)
            return

        try:
            admin_record = be.verify_admin_login_csv(username, password)
            
            if admin_record:
                messagebox.showinfo("Success", f"Admin login successful! Welcome {admin_record.get('username')}.", 
                                  parent=login_win)
                login_win.destroy()
                open_admin_panel()
            else:
                messagebox.showerror("Error", "Invalid admin credentials.", parent=login_win)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during admin login: {e}", parent=login_win)

    tk.Button(form_frame, text="Login", command=admin_login_check, bg="#FF5722", fg="white",
              font=("Helvetica", 12, "bold"), height=2).pack(pady=10, fill="x")

# ========================== MAIN WINDOW ==============================

def create_main_window():
    root = tk.Tk()
    root.title("Citizen Aid Management System")
    root.geometry("600x500")
    root.configure(bg="#f0f0f0")

    # Header
    header_frame = tk.Frame(root, bg="#3F51B5", height=100)
    header_frame.pack(fill="x")
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="Citizen Aid Management System", 
             font=("Helvetica", 20, "bold"), bg="#3F51B5", fg="white").pack(expand=True)

    # Main content
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(expand=True, fill="both", pady=30)

    tk.Label(main_frame, text="Welcome to the Citizen Aid Management System", 
             font=("Helvetica", 16), bg="#f0f0f0").pack(pady=20)
    
    tk.Label(main_frame, text="Please select your role:", 
             font=("Helvetica", 14), bg="#f0f0f0").pack(pady=10)

    # Button frame
    button_frame = tk.Frame(main_frame, bg="#f0f0f0")
    button_frame.pack(pady=30)

    tk.Button(button_frame, text="👤 Citizen Login", command=open_citizen_login,
              font=("Helvetica", 14, "bold"), bg="#4CAF50", fg="white", 
              width=20, height=2).pack(pady=10)
    
    tk.Button(button_frame, text="🔧 Admin Login", command=open_admin_login,
              font=("Helvetica", 14, "bold"), bg="#FF5722", fg="white", 
              width=20, height=2).pack(pady=10)
    
    tk.Button(button_frame, text="📝 Register New Citizen", command=open_register_screen,
              font=("Helvetica", 14, "bold"), bg="#2196F3", fg="white", 
              width=20, height=2).pack(pady=10)

    # Footer
    footer_frame = tk.Frame(root, bg="#3F51B5", height=40)
    footer_frame.pack(fill="x", side="bottom")
    footer_frame.pack_propagate(False)
    
    tk.Label(footer_frame, text="© 2024 Citizen Aid Management System", 
             font=("Helvetica", 10), bg="#3F51B5", fg="white").pack(expand=True)

    return root

# ========================== MAIN EXECUTION ==============================

if __name__ == "__main__":
    # Initialize backend
    be.setup_csv_files()
    
    # Create and run the main application
    root = create_main_window()
    root.mainloop()
