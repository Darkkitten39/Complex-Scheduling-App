import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import os
from tkinter import filedialog
from PIL import Image, ImageTk
import traceback
from datetime import datetime, timedelta, time, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import mariadb
from datetime import datetime
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import tempfile
import subprocess


# If modifying these SCOPES, delete the token.json file
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


theme_mode = "light"

# At the very top, create root ONCE
root = tk.Tk()
root.withdraw()  # Hide main window until DB connection is successful

def toggle_theme():
    global theme_mode
    if theme_mode == "dark":
        theme_mode = "light"
        apply_light_theme()
    else:
        theme_mode = "dark"
        apply_dark_theme()
    update_fonts_and_colors()

# Global variables
current_start_date = datetime.now().strftime("%Y-%m-%d")
current_end_date = datetime.now().strftime("%Y-%m-%d")

# Initialize tkinter variables after creating the root window
view_mode_var = tk.StringVar(value="Daily")



# Part 2: Database Connection and Utility Functions

# Global DB config (will be set by the connection screen)
db_config = {
    "user": "",
    "password": "",
    "host": "",
    "port": 3306,
    "database": ""
}

def show_connection_screen():
    conn_win = tk.Toplevel(root)  # Use Toplevel, not Tk
    conn_win.title("Database Connection")
    conn_win.geometry("350x300")
    # Entry fields for DB connection
    tk.Label(conn_win, text="Host:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
    host_entry = tk.Entry(conn_win)
    host_entry.grid(row=0, column=1, padx=10, pady=10)
    host_entry.insert(0, "localhost")

    tk.Label(conn_win, text="Port:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
    port_entry = tk.Entry(conn_win)
    port_entry.grid(row=1, column=1, padx=10, pady=10)
    port_entry.insert(0, "3306")

    tk.Label(conn_win, text="User:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
    user_entry = tk.Entry(conn_win)
    user_entry.grid(row=2, column=1, padx=10, pady=10)

    tk.Label(conn_win, text="Password:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
    password_entry = tk.Entry(conn_win, show="*")
    password_entry.grid(row=3, column=1, padx=10, pady=10)

    tk.Label(conn_win, text="Database:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
    db_entry = tk.Entry(conn_win)
    db_entry.grid(row=4, column=1, padx=10, pady=10)

    def try_connect():
        db_config["host"] = host_entry.get().strip()
        db_config["port"] = int(port_entry.get().strip())
        db_config["user"] = user_entry.get().strip()
        db_config["password"] = password_entry.get().strip()
        db_config["database"] = db_entry.get().strip()
        try:
            import mariadb
            connection = mariadb.connect(
                user=db_config["user"],
                password=db_config["password"],
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["database"]
            )
            connection.close()
            conn_win.destroy()
            root.deiconify()  # Show main window
            launch_main_app()
        except Exception as e:
            messagebox.showerror("Connection Failed", f"Could not connect to database:\n{e}")

    tk.Button(conn_win, text="Connect", command=try_connect).grid(row=5, column=0, columnspan=2, pady=20)

    conn_win.mainloop()

def connect_to_database():
    try:
        import mariadb
        connection = mariadb.connect(
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"]
        )
        print("Database connection successful!")
        return connection
    except mariadb.Error as e:
        print("Error connecting to the database:", e)
        messagebox.showerror("Database Error", f"Error connecting to database: {e}")
        return None

def launch_main_app():
    # Do NOT create root = tk.Tk() here!
    root.title("Schedule Manager")
    root.geometry("1200x800")

        # Add this after you create root = tk.Tk()
    menubar = tk.Menu(root)
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Clear Default Sender Data", command=clear_default_sender_data)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    root.config(menu=menubar)

    setup_layout()
    fetch_events()
    update_fonts_and_colors()
    auto_refresh()
    # Do NOT call root.mainloop() here if already called at the end

def fetch_employee_names():
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT EmployeeID, FirstName, LastName FROM Employees')
            employees = {}
            for row in cursor.fetchall():
                try:
                    if isinstance(row[0], int):
                        employee_id = row[0]
                    else:
                        raise ValueError(f"Invalid EmployeeID: {row[0]}")
                    first_name = row[1].strip() if row[1] else ""
                    last_name = row[2].strip() if row[2] else ""
                    if not first_name or not last_name:
                        raise ValueError("Invalid name fields")
                    full_name = f"{first_name} {last_name}"
                    employees[employee_id] = full_name
                except (ValueError, IndexError) as e:
                    print(f"Error processing employee record {row}: {e}")
            connection.close()
            return employees
        else:
            return {}
    except Exception as e:
        print("Error fetching employee names:", e)
        traceback.print_exc()
        return {}

def insert_employee(first_name, last_name, email, phone, address, picture, position, date_hired, notes):
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            query = '''
                INSERT INTO Employees (FirstName, LastName, Email, Phone, Address, Picture, Position, DateHired, Notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, (first_name, last_name, email, phone, address, picture, position, date_hired, notes))
            connection.commit()
            print("Employee added successfully!")
            connection.close()
    except Exception as e:
        print("Error inserting employee:", e)
        traceback.print_exc()

def fetch_employees():
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT EmployeeID, FirstName, LastName, Email, Phone FROM Employees')
            employees = cursor.fetchall()
            connection.close()
            return employees
        else:
            return []
    except Exception as e:
        print("Error fetching employees:", e)
        traceback.print_exc()
        return []

def fetch_client_names():
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT ClientID, ClientName FROM Clients')
            clients = {row[0]: row[1] for row in cursor.fetchall()}
            connection.close()
            return clients
        else:
            return {}
    except Exception as e:
        print("Error fetching client names:", e)
        traceback.print_exc()
        return {}

def open_add_employee_window(employee_tree):
    def add_employee():
        # Collect data from the fields
        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        address = address_entry.get().strip()
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        zip_code = zip_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()
        dl_number = dl_entry.get().strip()
        position = position_entry.get().strip()
        notes = notes_entry.get("1.0", tk.END).strip()

        # Combine address fields into a single string
        full_address = f"{address}, {city}, {state}, {zip_code}".strip(", ")

        # Validate required fields
        if not first_name or not last_name or not email or not phone or not position:
            messagebox.showwarning("Input Error", "Please fill in all required fields.")
            return

        try:
            # Insert the employee into the database
            insert_employee(
                first_name, last_name, email, phone, full_address, None, position,
                datetime.now().strftime("%Y-%m-%d"), notes
            )
            messagebox.showinfo("Success", "Employee added successfully!")
            add_employee_window.destroy()
            # Refresh the employee list
            populate_employees(employee_tree)
        except Exception as e:
            print("Error adding employee:", e)
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error adding employee: {e}")

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    # Create a pop-up window for adding an employee
    add_employee_window = tk.Toplevel(root)
    add_employee_window.title("Add Employee")
    add_employee_window.geometry("750x450")
    add_employee_window.configure(bg=bg_color)

    # Labels and Entry fields for employee details
    tk.Label(add_employee_window, text="Last Name:", bg=bg_color, fg=fg_color).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    last_name_entry = tk.Entry(add_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    last_name_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(add_employee_window, text="First Name:", bg=bg_color, fg=fg_color).grid(row=0, column=2, padx=10, pady=5, sticky="e")
    first_name_entry = tk.Entry(add_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    first_name_entry.grid(row=0, column=3, padx=10, pady=5)

    tk.Label(add_employee_window, text="Address:", bg=bg_color, fg=fg_color).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    address_entry = tk.Entry(add_employee_window, width=60, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    address_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=5)

    tk.Label(add_employee_window, text="City:", bg=bg_color, fg=fg_color).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    city_entry = tk.Entry(add_employee_window, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    tk.Label(add_employee_window, text="State:", bg=bg_color, fg=fg_color).grid(row=2, column=2, padx=10, pady=5, sticky="e")
    state_entry = tk.Entry(add_employee_window, width=10, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    state_entry.grid(row=2, column=3, padx=10, pady=5, sticky="w")

    tk.Label(add_employee_window, text="Zip:", bg=bg_color, fg=fg_color).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    zip_entry = tk.Entry(add_employee_window, width=10, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    zip_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

    tk.Label(add_employee_window, text="Phone:", bg=bg_color, fg=fg_color).grid(row=4, column=0, padx=10, pady=5, sticky="e")
    phone_entry = tk.Entry(add_employee_window, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    phone_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

    tk.Label(add_employee_window, text="Email:", bg=bg_color, fg=fg_color).grid(row=4, column=2, padx=10, pady=5, sticky="e")
    email_entry = tk.Entry(add_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    email_entry.grid(row=4, column=3, padx=10, pady=5)

    tk.Label(add_employee_window, text="DL Number:", bg=bg_color, fg=fg_color).grid(row=5, column=0, padx=10, pady=5, sticky="e")
    dl_entry = tk.Entry(add_employee_window, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    dl_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

    tk.Label(add_employee_window, text="Position:", bg=bg_color, fg=fg_color).grid(row=5, column=2, padx=10, pady=5, sticky="e")
    position_entry = tk.Entry(add_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    position_entry.grid(row=5, column=3, padx=10, pady=5)

    tk.Label(add_employee_window, text="Notes:", bg=bg_color, fg=fg_color).grid(row=6, column=0, padx=10, pady=5, sticky="e")
    notes_entry = tk.Text(add_employee_window, width=50, height=5, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    notes_entry.grid(row=6, column=1, columnspan=3, padx=10, pady=5)

    # Buttons for saving or canceling
    tk.Button(add_employee_window, text="Save", command=add_employee, bg=entry_bg, fg=entry_fg).grid(row=7, column=1, pady=20)
    tk.Button(add_employee_window, text="Cancel", command=add_employee_window.destroy, bg=entry_bg, fg=entry_fg).grid(row=7, column=2, pady=20)

def populate_employees(employee_tree):
    employee_tree.delete(*employee_tree.get_children())
    employees = fetch_employees()
    for emp in employees:
        try:
            # Ensure EmployeeID is valid
            employee_id = int(emp[0])
            employee_tree.insert("", "end", values=emp)
        except (ValueError, IndexError) as e:
            print(f"Error inserting employee into Treeview: {emp}, Error: {e}")

def prompt_gmail_auth():
    # Remove the old token to force re-auth
    if os.path.exists(get_token_path()):
        os.remove(get_token_path())
    try:
        get_gmail_service()  # This will prompt the OAuth screen
        messagebox.showinfo("Success", "Default sender updated! You are now authenticated with the selected Google account.")
    except Exception as e:
        print("Error during Google authentication:", e)
        messagebox.showerror("Auth Error", f"Error during Google authentication: {e}")            

def create_employees_tab(tab):
    # Create a LabelFrame for employee management
    employee_frame = ttk.LabelFrame(tab, text="Manage Employees")
    employee_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Treeview to display employees
    employee_tree = ttk.Treeview(employee_frame, columns=("ID", "First Name", "Last Name", "Email", "Phone"), show="headings")
    employee_tree.heading("ID", text="ID")
    employee_tree.heading("First Name", text="First Name")
    employee_tree.heading("Last Name", text="Last Name")
    employee_tree.heading("Email", text="Email")
    employee_tree.heading("Phone", text="Phone")
    employee_tree.column("ID", width=50)
    employee_tree.column("First Name", width=150)
    employee_tree.column("Last Name", width=150)
    employee_tree.column("Email", width=200)
    employee_tree.column("Phone", width=150)
    employee_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Apply dark theme to Treeview
    style = ttk.Style()
    style.configure("Treeview", background="#121212", foreground="#ffffff", fieldbackground="#121212")
    style.configure("Treeview.Heading", background="#333333", foreground="#ffffff")

    # Buttons for managing employees
    button_frame = ttk.Frame(employee_frame)
    button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
    ttk.Button(button_frame, text="Add Employee", command=lambda: open_add_employee_window(employee_tree)).grid(row=0, column=0, padx=5)
    ttk.Button(button_frame, text="Remove Employee", command=lambda: remove_employee(employee_tree)).grid(row=0, column=1, padx=5)
    ttk.Button(button_frame, text="Update Employee", command=lambda: open_update_employee_window(employee_tree)).grid(row=0, column=2, padx=5)
    ttk.Button(button_frame, text="Refresh List", command=lambda: populate_employees(employee_tree)).grid(row=0, column=3, padx=5)
    ttk.Button(button_frame, text="Set as Default Sender", command=prompt_gmail_auth).grid(row=0, column=4, padx=5)

    # Configure grid for responsiveness
    employee_frame.grid_rowconfigure(0, weight=1)
    employee_frame.grid_columnconfigure(0, weight=1)

    # Populate the Treeview initially
    populate_employees(employee_tree)

def remove_employee(employee_tree):
    selected_item = employee_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select an employee to remove.")
        return

    employee_data = employee_tree.item(selected_item, "values")
    try:
        employee_id = int(str(employee_data[0]).strip("(), "))
    except (ValueError, IndexError) as e:
        messagebox.showerror("Error", "Invalid employee ID. Please try again.")
        print("Error extracting employee ID:", e)
        return
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            # Remove all recurring events for this employee
            cursor.execute('DELETE FROM RecurringEvents WHERE EmployeeID = ?', (employee_id,))
            # Remove all events for this employee (optional, or set EmployeeID to NULL)
            cursor.execute('UPDATE Events SET EmployeeID = NULL WHERE EmployeeID = ?', (employee_id,))
            # Now delete the employee
            cursor.execute('DELETE FROM Employees WHERE EmployeeID = ?', (employee_id,))
            connection.commit()
            print("Employee and related recurring events removed.")
            connection.close()
            employee_tree.delete(selected_item)
            messagebox.showinfo("Success", "Employee removed successfully!")
    except Exception as e:
        print("Error removing employee:", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error removing employee: {e}")

def open_update_employee_window(employee_tree):
    selected_item = employee_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select an employee to update.")
        return

    employee_data = employee_tree.item(selected_item, "values")
    try:
        employee_id = int(str(employee_data[0]).strip("(), "))  # Clean and convert to integer
    except (ValueError, IndexError) as e:
        messagebox.showerror("Error", "Invalid employee ID. Please try again.")
        print("Error extracting employee ID:", e)
        return

    # Fetch full employee details from the database
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            query = '''
                SELECT FirstName, LastName, Email, Phone, Position, Address, Notes
                FROM Employees
                WHERE EmployeeID = ?
            '''
            cursor.execute(query, (employee_id,))
            full_employee_data = cursor.fetchone()
            connection.close()
    except Exception as e:
        print("Error fetching employee details:", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error fetching employee details: {e}")
        return

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    # Create a pop-up window for updating the employee
    update_employee_window = tk.Toplevel(root)
    update_employee_window.title("Update Employee")
    update_employee_window.geometry("750x450")
    update_employee_window.configure(bg=bg_color)

    # Pre-fill the fields with the selected employee's data
    tk.Label(update_employee_window, text="Last Name:", bg=bg_color, fg=fg_color).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    last_name_entry = tk.Entry(update_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    last_name_entry.insert(0, full_employee_data[1])
    last_name_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(update_employee_window, text="First Name:", bg=bg_color, fg=fg_color).grid(row=0, column=2, padx=10, pady=5, sticky="e")
    first_name_entry = tk.Entry(update_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    first_name_entry.insert(0, full_employee_data[0])
    first_name_entry.grid(row=0, column=3, padx=10, pady=5)

    tk.Label(update_employee_window, text="Address:", bg=bg_color, fg=fg_color).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    address_entry = tk.Entry(update_employee_window, width=60, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    address_entry.insert(0, full_employee_data[5].split(",")[0])
    address_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=5)

    tk.Label(update_employee_window, text="City:", bg=bg_color, fg=fg_color).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    city_entry = tk.Entry(update_employee_window, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    city_entry.insert(0, full_employee_data[5].split(",")[1].strip())
    city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    tk.Label(update_employee_window, text="State:", bg=bg_color, fg=fg_color).grid(row=2, column=2, padx=10, pady=5, sticky="e")
    state_entry = tk.Entry(update_employee_window, width=10, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    state_entry.insert(0, full_employee_data[5].split(",")[2].strip())
    state_entry.grid(row=2, column=3, padx=10, pady=5, sticky="w")

    tk.Label(update_employee_window, text="Zip:", bg=bg_color, fg=fg_color).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    zip_entry = tk.Entry(update_employee_window, width=10, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    zip_entry.insert(0, full_employee_data[5].split(",")[3].strip())
    zip_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")

    tk.Label(update_employee_window, text="Phone:", bg=bg_color, fg=fg_color).grid(row=4, column=0, padx=10, pady=5, sticky="e")
    phone_entry = tk.Entry(update_employee_window, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    phone_entry.insert(0, full_employee_data[3])
    phone_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

    tk.Label(update_employee_window, text="Email:", bg=bg_color, fg=fg_color).grid(row=4, column=2, padx=10, pady=5, sticky="e")
    email_entry = tk.Entry(update_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    email_entry.insert(0, full_employee_data[2])
    email_entry.grid(row=4, column=3, padx=10, pady=5)

    tk.Label(update_employee_window, text="Position:", bg=bg_color, fg=fg_color).grid(row=5, column=0, padx=10, pady=5, sticky="e")
    position_entry = tk.Entry(update_employee_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    position_entry.insert(0, full_employee_data[4])
    position_entry.grid(row=5, column=1, padx=10, pady=5)

    tk.Label(update_employee_window, text="Notes:", bg=bg_color, fg=fg_color).grid(row=6, column=0, padx=10, pady=5, sticky="e")
    notes_entry = tk.Text(update_employee_window, width=50, height=5, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    notes_entry.insert("1.0", full_employee_data[6])
    notes_entry.grid(row=6, column=1, columnspan=3, padx=10, pady=5)

    # Save changes to the database
    def save_changes():
        first_name = first_name_entry.get().strip()
        last_name = last_name_entry.get().strip()
        address = address_entry.get().strip()
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        zip_code = zip_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()
        position = position_entry.get().strip()
        notes = notes_entry.get("1.0", tk.END).strip()

        full_address = f"{address}, {city}, {state}, {zip_code}".strip(", ")

        if not first_name or not last_name or not email or not phone or not position:
            messagebox.showwarning("Input Error", "Please fill in all required fields.")
            return

        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                query = '''
                    UPDATE Employees
                    SET FirstName = ?, LastName = ?, Email = ?, Phone = ?, Address = ?, Position = ?, Notes = ?
                    WHERE EmployeeID = ?
                '''
                cursor.execute(query, (first_name, last_name, email, phone, full_address, position, notes, employee_id))
                connection.commit()
                connection.close()
                messagebox.showinfo("Success", "Employee updated successfully!")
                update_employee_window.destroy()
                populate_employees(employee_tree)  # Refresh the employee list
        except Exception as e:
            print("Error updating employee:", e)
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error updating employee: {e}")

    # Buttons for saving or canceling
    tk.Button(update_employee_window, text="Save Changes", command=save_changes, bg=entry_bg, fg=entry_fg).grid(row=7, column=1, pady=20)
    tk.Button(update_employee_window, text="Cancel", command=update_employee_window.destroy, bg=entry_bg, fg=entry_fg).grid(row=7, column=2, pady=20)

def open_employee_profile_window(employee_data=None):
    # Create a pop-up window for adding or updating an employee
    profile_window = tk.Toplevel(root)
    profile_window.title("Employee Profile")
    profile_window.geometry("500x500")

    # Labels and Entry fields for employee details
    tk.Label(profile_window, text="Last Name:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    last_name_entry = tk.Entry(profile_window, width=30)
    last_name_entry.grid(row=0, column=1, padx=10, pady=5)
    if employee_data:
        last_name_entry.insert(0, employee_data.get("last_name", ""))

    tk.Label(profile_window, text="First Name:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
    first_name_entry = tk.Entry(profile_window, width=30)
    first_name_entry.grid(row=0, column=3, padx=10, pady=5)
    if employee_data:
        first_name_entry.insert(0, employee_data.get("first_name", ""))

    tk.Label(profile_window, text="Address:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    address_entry = tk.Entry(profile_window, width=60)
    address_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=5)
    if employee_data:
        address_entry.insert(0, employee_data.get("address", ""))

    tk.Label(profile_window, text="City:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
    city_entry = tk.Entry(profile_window, width=20)
    city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        city_entry.insert(0, employee_data.get("city", ""))

    tk.Label(profile_window, text="State:").grid(row=2, column=2, padx=10, pady=5, sticky="e")
    state_entry = tk.Entry(profile_window, width=10)
    state_entry.grid(row=2, column=3, padx=10, pady=5, sticky="w")
    if employee_data:
        state_entry.insert(0, employee_data.get("state", ""))

    tk.Label(profile_window, text="Zip:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
    zip_entry = tk.Entry(profile_window, width=10)
    zip_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        zip_entry.insert(0, employee_data.get("zip", ""))

    tk.Label(profile_window, text="Phone:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
    phone_entry = tk.Entry(profile_window, width=20)
    phone_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        phone_entry.insert(0, employee_data.get("phone", ""))

    tk.Label(profile_window, text="Email:").grid(row=4, column=2, padx=10, pady=5, sticky="e")
    email_entry = tk.Entry(profile_window, width=30)
    email_entry.grid(row=4, column=3, padx=10, pady=5)
    if employee_data:
        email_entry.insert(0, employee_data.get("email", ""))

    tk.Label(profile_window, text="DL Number:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
    dl_entry = tk.Entry(profile_window, width=20)
    dl_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        dl_entry.insert(0, employee_data.get("dl_number", ""))

    # Buttons for saving or canceling
    def save_employee():
        # Collect data from the fields
        employee_details = {
            "last_name": last_name_entry.get(),
            "first_name": first_name_entry.get(),
            "address": address_entry.get(),
            "city": city_entry.get(),
            "state": state_entry.get(),
            "zip": zip_entry.get(),
            "phone": phone_entry.get(),
            "email": email_entry.get(),
            "dl_number": dl_entry.get(),
        }
        print("Employee Details Saved:", employee_details)  # Debugging statement
        profile_window.destroy()

    tk.Button(profile_window, text="Save", command=save_employee).grid(row=6, column=1, pady=20)
    tk.Button(profile_window, text="Cancel", command=profile_window.destroy).grid(row=6, column=2, pady=20)

def create_clients_tab(tab):
    # Create a LabelFrame for client management
    client_frame = ttk.LabelFrame(tab, text="Manage Clients")
    client_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Treeview to display clients (now includes Address column)
    client_tree = ttk.Treeview(
        client_frame,
        columns=("ID", "ClientName", "Email", "Phone", "Address"),
        show="headings"
    )
    client_tree.heading("ID", text="ID")
    client_tree.heading("ClientName", text="Client Name")
    client_tree.heading("Email", text="Email")
    client_tree.heading("Phone", text="Phone")
    client_tree.heading("Address", text="Address")
    client_tree.column("ID", width=50)
    client_tree.column("ClientName", width=200)
    client_tree.column("Email", width=200)
    client_tree.column("Phone", width=150)
    client_tree.column("Address", width=250)
    client_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Apply theme to Treeview
    style = ttk.Style()
    if theme_mode == "dark":
        style.configure("Treeview", background="#121212", foreground="#ffffff", fieldbackground="#121212")
        style.configure("Treeview.Heading", background="#333333", foreground="#ffffff")
    else:
        style.configure("Treeview", background="#ffffff", foreground="#000000", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", background="#e0e0e0", foreground="#000000")

    # Buttons for managing clients
    button_frame = ttk.Frame(client_frame)
    button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
    ttk.Button(button_frame, text="Add Client", command=lambda: open_client_profile_window_combined(mode="add", client_tree=client_tree)).grid(row=0, column=0, padx=5)
    ttk.Button(button_frame, text="Delete Client", command=lambda: remove_client(client_tree)).grid(row=0, column=1, padx=5)
    ttk.Button(button_frame, text="View Profile", command=lambda: view_client_profile(client_tree)).grid(row=0, column=2, padx=5)
    ttk.Button(button_frame, text="Refresh List", command=lambda: populate_clients(client_tree)).grid(row=0, column=3, padx=5)
    ttk.Button(button_frame, text="Email Selected Client", command=lambda: open_email_draft_window(client_tree)).grid(row=0, column=4, padx=5)

    # Configure grid for responsiveness
    client_frame.grid_rowconfigure(0, weight=1)
    client_frame.grid_columnconfigure(0, weight=1)

    # Populate the Treeview initially
    populate_clients(client_tree)

def populate_clients(client_tree):
    client_tree.delete(*client_tree.get_children())
    clients = fetch_clients()
    for client in clients:
        # Display: ClientID, ClientName, Email, Phone, Address
        client_tree.insert("", "end", values=(client[0], client[1], client[2], client[3], client[5]))

def fetch_clients():
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT ClientID, ClientName, Email, Phone, Picture, Address, Company, Notes, CleaningSuppliesNeeded, Comments, EmailQueuePrompt FROM Clients')
            clients = cursor.fetchall()
            connection.close()
            return clients
        else:
            return []  # Return empty list if connection fails
    except Exception as e:
        print("Error fetching clients:", e)
        traceback.print_exc()
        return {}

def open_client_profile_window_combined(mode="view", client_data=None, client_tree=None, parent_win=None):
    """
    mode: "view", "update", or "add"
    client_data: tuple from DB (for view/update), or None for add
    client_tree: Treeview widget for refreshing after add/update
    parent_win: parent window to destroy after update (optional)
    """
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    win = tk.Toplevel(root)
    win.title(
        "Add Client" if mode == "add" else
        "Update Client" if mode == "update" else
        "Client Profile"
    )
    win.geometry("900x650")
    win.configure(bg=bg_color)

    def open_update_popup():
        win.destroy()
        open_client_profile_window_combined(
            mode="update",
            client_data=client_data,
            client_tree=client_tree,
            parent_win=parent_win
        )

    gallery_images_data = []  # Store gallery images data

    settings_btn = tk.Menubutton(win, text="⚙ Settings", bg=bg_color, fg=fg_color, relief="raised")
    settings_menu = tk.Menu(settings_btn, tearoff=0, bg=entry_bg, fg=entry_fg)
    settings_menu.add_command(label="Update", command=open_update_popup)
    settings_btn.config(menu=settings_menu)
    settings_btn.grid(row=0, column=99, padx=10, pady=10, sticky="ne")

    # --- Client Photo ---
    tk.Label(win, text="Client Photo:", bg=bg_color, fg=fg_color).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    photo_frame = tk.Frame(win, bg=bg_color, width=120, height=120, highlightbackground=fg_color, highlightthickness=2)
    photo_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    client_photo_label = tk.Label(photo_frame, bg=bg_color)
    client_photo_label.pack(expand=True)
    client_photo_img = None
    client_photo_data = None
    if client_data and len(client_data) > 4 and client_data[4]:
        try:
            image = Image.open(io.BytesIO(client_data[4]))
            image.thumbnail((120, 120))
            client_photo_img = ImageTk.PhotoImage(image)
            client_photo_label.config(image=client_photo_img)
            client_photo_label.image = client_photo_img
            client_photo_data = client_data[4]
        except Exception as e:
            print("Error loading client photo:", e)

    def upload_client_photo():
        nonlocal client_photo_img, client_photo_data
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            img = Image.open(file_path)
            img.thumbnail((120, 120))
            client_photo_img = ImageTk.PhotoImage(img)
            client_photo_label.config(image=client_photo_img)
            client_photo_label.image = client_photo_img
            with open(file_path, "rb") as f:
                client_photo_data = f.read()

    if mode in ("add", "update"):
        tk.Button(win, text="Upload Photo", command=upload_client_photo, bg=entry_bg, fg=entry_fg).grid(row=0, column=2, padx=10, pady=10, sticky="w")

    # --- Client Name ---
    tk.Label(win, text="Client Name:", bg=bg_color, fg=fg_color).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    name_entry = tk.Entry(
        win, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg,
        disabledbackground=entry_bg, disabledforeground=entry_fg
    )
    name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 1:
        name_entry.insert(0, client_data[1])
    if mode == "view":
        name_entry.config(state="disabled")

    # --- Phone ---
    tk.Label(win, text="Phone:", bg=bg_color, fg=fg_color).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    phone_entry = tk.Entry(
        win, width=20, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg,
        disabledbackground=entry_bg, disabledforeground=entry_fg
    )
    phone_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 3:
        phone_entry.insert(0, client_data[3])
    if mode == "view":
        phone_entry.config(state="disabled")

    # --- Email ---
    tk.Label(win, text="Email:", bg=bg_color, fg=fg_color).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    email_entry = tk.Entry(
        win, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg,
        disabledbackground=entry_bg, disabledforeground=entry_fg
    )
    email_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 2:
        email_entry.insert(0, client_data[2])
    if mode == "view":
        email_entry.config(state="disabled")

    # --- Address ---
    tk.Label(win, text="Address:", bg=bg_color, fg=fg_color).grid(row=4, column=0, padx=10, pady=5, sticky="e")
    address_entry = tk.Entry(
        win, width=50, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg,
        disabledbackground=entry_bg, disabledforeground=entry_fg
    )
    address_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 5:
        address_entry.insert(0, client_data[5])
    if mode == "view":
        address_entry.config(state="disabled")

    # --- Cleaning Supplies Needed ---
    tk.Label(win, text="Cleaning Supplies Needed:", bg=bg_color, fg=fg_color).grid(row=5, column=0, padx=10, pady=5, sticky="ne")
    supplies_entry = tk.Text(win, width=30, height=2, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    supplies_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 8:
        supplies_entry.insert("1.0", client_data[8] or "")
    if mode == "view":
        supplies_entry.config(state="disabled")

    # --- Comments ---
    tk.Label(win, text="Comments:", bg=bg_color, fg=fg_color).grid(row=6, column=0, padx=10, pady=5, sticky="ne")
    comments_entry = tk.Text(win, width=30, height=2, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    comments_entry.grid(row=6, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 9:
        comments_entry.insert("1.0", client_data[9] or "")
    if mode == "view":
        comments_entry.config(state="disabled")

    # --- Upcoming Events ---
    tk.Label(win, text="Upcoming Event:", bg=bg_color, fg=fg_color).grid(row=7, column=0, padx=10, pady=5, sticky="ne")
    upcoming_event_var = tk.StringVar(value="Loading...")
    upcoming_event_label = tk.Label(win, textvariable=upcoming_event_var, bg=entry_bg, fg=entry_fg, anchor="w", width=40)
    upcoming_event_label.grid(row=7, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 1:
        client_name = client_data[1]
        upcoming_event_var.set(get_next_event_for_client(client_name))
    else:
        upcoming_event_var.set("No client selected")

    # --- Notes ---
    tk.Label(win, text="Notes:", bg=bg_color, fg=fg_color).grid(row=9, column=0, padx=10, pady=5, sticky="ne")
    notes_entry = tk.Text(win, width=50, height=3, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    notes_entry.grid(row=9, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 7:
        notes_entry.insert("1.0", client_data[7] or "")
    if mode == "view":
        notes_entry.config(state="disabled")

    # --- Email Queue Prompt ---
    tk.Label(win, text="Email Queue Prompt:", bg=bg_color, fg=fg_color).grid(row=10, column=0, padx=10, pady=5, sticky="ne")
    email_queue_entry = tk.Text(win, width=30, height=2, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    email_queue_entry.grid(row=10, column=1, padx=10, pady=5, sticky="w")
    if client_data and len(client_data) > 11:
        email_queue_entry.insert("1.0", client_data[11] or "")
    if mode == "view":
        email_queue_entry.config(state="disabled")

    def upload_pictures():
        files = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        for file_path in files:
            with open(file_path, "rb") as f:
                gallery_images_data.append((os.path.basename(file_path), f.read()))

    def view_pictures():
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix="client_pics_")
        image_paths = []
        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                cursor.execute("SELECT FileName, Picture FROM ClientPictures WHERE ClientID = ?", (client_data[0],))
                for file_name, img_blob in cursor.fetchall():
                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, "wb") as f:
                        f.write(img_blob)
                    image_paths.append(file_path)
                connection.close()
            if image_paths:
                subprocess.Popen(f'explorer "{temp_dir}"')
            else:
                messagebox.showinfo("No Pictures", "No pictures found for this client.")
        except Exception as e:
            print("Error extracting and opening pictures:", e)
            messagebox.showerror("Error", f"Error opening pictures: {e}")

    tk.Button(win, text="View Pictures", command=view_pictures, bg=entry_bg, fg=entry_fg).grid(row=8, column=1, padx=10, pady=5, sticky="w")
    if mode in ("add", "update"):
        tk.Button(
            win,
            text="Upload Pictures",
            command=upload_pictures,
            bg=entry_bg,
            fg=entry_fg
        ).grid(row=8, column=2, padx=10, pady=5, sticky="w")

    # --- Save logic ---
    def save_client():
        client_name = name_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()
        address = address_entry.get().strip()
        cleaning_supplies = supplies_entry.get("1.0", tk.END).strip()
        comments = comments_entry.get("1.0", tk.END).strip()
        notes = notes_entry.get("1.0", tk.END).strip()
        email_queue = email_queue_entry.get("1.0", tk.END).strip()
        picture = client_photo_data  # Save as BLOB

        if not client_name:
            messagebox.showwarning("Input Error", "Please enter the client name.")
            return
        if not email:
            messagebox.showwarning("Input Error", "Please enter the client email.")
            return

        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                if mode == "add":
                    cursor.execute("SELECT COUNT(*) FROM Clients WHERE Email = ?", (email,))
                    if cursor.fetchone()[0] > 0:
                        messagebox.showerror("Duplicate Error", "A client with this email already exists.")
                        connection.close()
                        return
                    print("Saving EmailQueuePrompt:", repr(email_queue))
                    cursor.execute('''
                        INSERT INTO Clients (ClientName, Email, Phone, Picture, Address, Notes, CleaningSuppliesNeeded, Comments, EmailQueuePrompt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (client_name, email, phone, picture, address, notes, cleaning_supplies, comments, email_queue))
                    client_id = cursor.lastrowid
                    # Save gallery images
                    if gallery_images_data:
                        for file_name, img_data in gallery_images_data:
                            cursor.execute(
                                "INSERT INTO ClientPictures (ClientID, FileName, Picture) VALUES (?, ?, ?)",
                                (client_id, file_name, img_data)
                            )
                    connection.commit()
                    messagebox.showinfo("Success", "Client added successfully!")
                elif mode == "update":
                    cursor.execute('''
                        UPDATE Clients
                        SET ClientName=?, Email=?, Phone=?, Picture=?, Address=?, Notes=?, CleaningSuppliesNeeded=?, Comments=?, EmailQueuePrompt=?
                        WHERE ClientID=?
                    ''', (client_name, email, phone, picture, address, notes, cleaning_supplies, comments, email_queue, client_data[0]))
                    client_id = client_data[0]
                    # Save new gallery images
                    if gallery_images_data:
                        for file_name, img_data in gallery_images_data:
                            cursor.execute(
                                "INSERT INTO ClientPictures (ClientID, FileName, Picture) VALUES (?, ?, ?)",
                                (client_id, file_name, img_data)
                            )
                    connection.commit()
                    messagebox.showinfo("Success", "Client updated successfully!")
                connection.close()
                win.destroy()
                if parent_win:
                    parent_win.destroy()
                if client_tree:
                    populate_clients(client_tree)
        except Exception as e:
            print("Error saving/updating client:", e)
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error saving/updating client: {e}")

    if mode in ("add", "update"):
        tk.Button(
            win, text="Save", command=save_client, bg=entry_bg, fg=entry_fg
        ).grid(row=11, column=1, pady=20)
        tk.Button(
            win, text="Cancel", command=win.destroy, bg=entry_bg, fg=entry_fg
        ).grid(row=11, column=2, pady=20)

def view_client_profile(client_tree):
    selected_item = client_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a client to view.")
        return
    client_data = client_tree.item(selected_item, "values")
    # Fetch full client details from the database
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT ClientID, ClientName, Email, Phone, Picture, Address, Company, Notes,
                       CleaningSuppliesNeeded, Comments, EmailQueuePrompt
                FROM Clients WHERE ClientID = ?
            ''', (client_data[0],))
            full_client_data = cursor.fetchone()
            connection.close()
            if full_client_data:
                open_client_profile_window_combined(mode="view", client_data=full_client_data)
            else:
                messagebox.showerror("Error", "Could not find client details.")
    except Exception as e:
        print("Error fetching client details:", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error fetching client details: {e}")

def remove_client(client_tree):
    selected_item = client_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a client to remove.")
        return
    client_data = client_tree.item(selected_item, "values")
    try:
        client_id = int(str(client_data[0]).strip("(), "))
    except (ValueError, IndexError) as e:
        messagebox.showerror("Error", "Invalid client ID. Please try again.")
        print("Error extracting client ID:", e)
        return
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            # First, delete all events for this client
            cursor.execute('DELETE FROM Events WHERE ClientID = ?', (client_id,))
            # Then, delete all recurring events for this client
            cursor.execute('DELETE FROM RecurringEvents WHERE ClientID = ?', (client_id,))
            # Then, delete all pictures for this client
            cursor.execute('DELETE FROM ClientPictures WHERE ClientID = ?', (client_id,))
            # Now delete the client
            cursor.execute('DELETE FROM Clients WHERE ClientID = ?', (client_id,))
            connection.commit()
            connection.close()
            client_tree.delete(selected_item)
            messagebox.showinfo("Success", "Client removed successfully!")
    except Exception as e:
        print("Error removing client:", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error removing client: {e}")

def open_manage_recurring_events_window():
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    win = tk.Toplevel(root)
    win.title("Manage Recurring Events")
    win.geometry("700x400")
    win.configure(bg=bg_color)

    tree = ttk.Treeview(win, columns=("ID", "Pattern", "Interval", "Start", "End", "Name"), show="headings")
    for col in ("ID", "Pattern", "Interval", "Start", "End", "Name"):
        tree.heading(col, text=col)
    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # Populate tree
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT RecurringID, Pattern, Interval, StartDate, EndDate, EventName FROM RecurringEvents")
            for row in cursor.fetchall():
                # Unpack and format each value
                recurring_id = row[0]
                pattern = str(row[1]).capitalize() if row[1] else ""
                interval = int(row[2]) if row[2] is not None else ""
                start = row[3].strftime("%Y-%m-%d") if hasattr(row[3], "strftime") else str(row[3])
                end = row[4].strftime("%Y-%m-%d") if hasattr(row[4], "strftime") else (row[4] if row[4] else "")
                name = row[5] if row[5] else ""
                tree.insert("", "end", values=(recurring_id, pattern, interval, start, end, name))
            connection.close()
    except Exception as e:
        print("Error fetching recurring events:", e)

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a recurring event to delete.")
            return
        recurring_id = tree.item(selected[0], "values")[0]
        # Make sure recurring_id is an int
        try:
            recurring_id = int(str(recurring_id).replace(",", "").strip())
        except Exception:
            messagebox.showerror("Error", "Invalid Recurring ID.")
            return
        if messagebox.askyesno("Delete", "Delete all future events for this recurrence?"):
            try:
                connection = connect_to_database()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("DELETE FROM Events WHERE RecurringID = ?", (recurring_id,))
                    cursor.execute("DELETE FROM RecurringEvents WHERE RecurringID = ?", (recurring_id,))
                    connection.commit()
                    connection.close()
                    tree.delete(selected[0])
                    fetch_events()  # <-- Add this line to refresh the schedule view
                    messagebox.showinfo("Success", "Recurring event and all future events deleted.")
            except Exception as e:
                print("Error deleting recurring event:", e)
                messagebox.showerror("Error", str(e))

    tk.Button(win, text="Delete Selected", command=delete_selected, bg="#e53935", fg="#fff").pack(pady=10)

def get_next_event_for_client(client_name):
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            # First, get the ClientID for this client name
            cursor.execute('SELECT ClientID FROM Clients WHERE ClientName = ?', (client_name,))
            row = cursor.fetchone()
            if not row:
                connection.close()
                return "Client not found"
            client_id = row[0]
            # Now, find the soonest event for this client after today
            cursor.execute('''
                SELECT EventName, EventDate, EventStartTime
                FROM Events
                WHERE ClientID = ? AND EventDate >= ?
                ORDER BY EventDate ASC, EventStartTime ASC
            ''', (client_id, datetime.now().strftime("%Y-%m-%d")))
            next_event = cursor.fetchone()
            connection.close()
            if next_event:
                # Format the date as MM/DD/YYYY
                event_name = next_event[0]
                event_date = next_event[1]
                event_time = next_event[2]
                # Convert date to MM/DD/YYYY
                if isinstance(event_date, (datetime, date)):
                    date_str = event_date.strftime("%m/%d/%Y")
                else:
                    date_str = datetime.strptime(str(event_date), "%Y-%m-%d").strftime("%m/%d/%Y")
                return f"Cleaning for {event_name}, on {date_str}, at {event_time}"
            else:
                return "No upcoming events"
    except Exception as e:
        print("Error fetching next event for client:", e)
        return "Error"

def get_credentials_path():
    import os
    home = os.path.expanduser("~")
    cred_dir = os.path.join(home, ".my_schedule_app")
    os.makedirs(cred_dir, exist_ok=True)
    return os.path.join(cred_dir, "credentials.json")

def get_token_path():
    # Store token in user's home directory under a hidden folder
    home = os.path.expanduser("~")
    token_dir = os.path.join(home, ".my_schedule_app")
    os.makedirs(token_dir, exist_ok=True)
    return os.path.join(token_dir, "token.json")

def get_gmail_service():
    creds = None
    if os.path.exists(get_token_path()):
        creds = Credentials.from_authorized_user_file(get_token_path(), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(get_token_path(), 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_message(service, sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    message = service.users().messages().send(userId="me", body=body).execute()
    print('Message Id:', message['id'])
    return message

def send_event_complete_emails_for_today():
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            # Get all events for today with their client info
            cursor.execute('''
                SELECT Events.ClientID, Clients.Email, Clients.EmailQueuePrompt, Clients.ClientName
                FROM Events
                JOIN Clients ON Events.ClientID = Clients.ClientID
                WHERE Events.EventDate = ?
            ''', (today,))
            rows = cursor.fetchall()
            connection.close()
            if not rows:
                messagebox.showinfo("Info", "No events for today.")
                return

            service = get_gmail_service()
            sender_email = "youraddress@gmail.com"  # Replace with your Gmail address
            sent_count = 0
            for client_id, email, prompt, client_name in rows:
                if not email:
                    continue
                message_text = prompt or f"Thank you for your event today, {client_name}!"
                try:
                    send_message(
                        service,
                        sender=sender_email,
                        to=email,
                        subject=f"Thank you for your event today, {client_name}!",
                        message_text=message_text
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending email to {email}:", e)
            messagebox.showinfo("Success", f"Sent {sent_count} emails for today's events.")
    except Exception as e:
        print("Error sending event-complete emails:", e)
        messagebox.showerror("Error", f"Error sending event-complete emails: {e}")

def get_default_sender_email():
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT Email FROM Employees WHERE IsDefaultSender=1")
            row = cursor.fetchone()
            connection.close()
            if row:
                return row[0]
    except Exception as e:
        print("Error fetching default sender:", e)
    return "youraddress@gmail.com"  # fallback

def open_email_draft_window(client_tree):
    selected_item = client_tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select a client to email.")
        return

    client_data = client_tree.item(selected_item, "values")
    client_id = client_data[0]

    # Fetch client email from DB
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT Email FROM Clients WHERE ClientID = ?', (client_id,))
            row = cursor.fetchone()
            connection.close()
            if not row:
                messagebox.showerror("Error", "Could not find client details.")
                return
            recipient_email = row[0]
    except Exception as e:
        print("Error fetching client details:", e)
        messagebox.showerror("Database Error", f"Error fetching client details: {e}")
        return

    # Email draft popup
    draft_win = tk.Toplevel(root)
    draft_win.title("Compose Email")
    draft_win.geometry("500x400")

    tk.Label(draft_win, text="To:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    to_entry = tk.Entry(draft_win, width=40)
    to_entry.grid(row=0, column=1, padx=5, pady=5)
    to_entry.insert(0, recipient_email)

    tk.Label(draft_win, text="Subject:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    subject_entry = tk.Entry(draft_win, width=40)
    subject_entry.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(draft_win, text="Message:").grid(row=2, column=0, sticky="ne", padx=5, pady=5)
    message_text = tk.Text(draft_win, width=40, height=10)
    message_text.grid(row=2, column=1, padx=5, pady=5)

    attachments = []

    def add_attachment():
        files = filedialog.askopenfilenames(title="Select Attachments")
        attachments.extend(files)
        attach_label.config(text="; ".join([os.path.basename(f) for f in attachments]))

    attach_label = tk.Label(draft_win, text="", anchor="w")
    attach_label.grid(row=3, column=1, sticky="w", padx=5)

    tk.Button(draft_win, text="Add Attachment", command=add_attachment).grid(row=3, column=0, padx=5, pady=5)

    def send_custom_email():
        service = get_gmail_service()
        sender_email = get_default_sender_email()  # Implement this function to fetch from DB
        to = to_entry.get().strip()
        subject = subject_entry.get().strip()
        body = message_text.get("1.0", tk.END).strip()

        # Build the email with attachments
        msg = MIMEMultipart()
        msg['to'] = to
        msg['from'] = sender_email
        msg['subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        for file_path in attachments:
            with open(file_path, "rb") as f:
                part = MIMEText(f.read(), 'base64')
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body = {'raw': raw}
        try:
            service.users().messages().send(userId="me", body=body).execute()
            messagebox.showinfo("Success", "Email sent!")
            draft_win.destroy()
        except Exception as e:
            print("Error sending email:", e)
            messagebox.showerror("Email Error", f"Error sending email: {e}")

    tk.Button(draft_win, text="Send", command=send_custom_email).grid(row=4, column=1, pady=10)

# Part 3: Theme and Layout Setup
def apply_light_theme():
    style = ttk.Style()
    style.theme_use("clam")
    light_bg = "#ffffff"
    light_fg = "#000000"
    accent_color = "#1e88e5"
    button_bg = "#e0e0e0"
    button_hover = "#cccccc"

    style.configure("TFrame", background=light_bg)
    style.configure("TLabel", background=light_bg, foreground=light_fg)
    style.configure("TNotebook", background=light_bg, foreground=light_fg)
    style.configure("TNotebook.Tab", background=button_bg, foreground=light_fg)
    style.map("TNotebook.Tab", background=[("selected", accent_color)])
    style.configure("TButton", background=button_bg, foreground=light_fg, borderwidth=0)
    style.map("TButton", background=[("active", button_hover)])
    style.configure("Treeview", background=light_bg, foreground=light_fg, fieldbackground=light_bg)
    style.configure("Treeview.Heading", background=button_bg, foreground=light_fg)
    root.configure(bg=light_bg)

    # Update schedule_canvas background if it exists
    try:
        schedule_canvas.configure(bg="#ffffff")
    except Exception:
        pass

def apply_dark_theme():
    style = ttk.Style()
    style.theme_use("clam")  # Use a base theme to customize

    # Define dark colors
    dark_bg = "#121212"
    dark_fg = "#ffffff"
    accent_color = "#1e88e5"
    button_bg = "#333333"
    button_hover = "#444444"

    # Configure styles for ttk widgets
    style.configure("TFrame", background=dark_bg)
    style.configure("TLabel", background=dark_bg, foreground=dark_fg)
    style.configure("TNotebook", background=dark_bg, foreground=dark_fg)
    style.configure("TNotebook.Tab", background=button_bg, foreground=dark_fg)
    style.map("TNotebook.Tab", background=[("selected", accent_color)])
    style.configure("TButton", background=button_bg, foreground=dark_fg, borderwidth=0)
    style.map("TButton", background=[("active", button_hover)])
    style.configure("Treeview", background=dark_bg, foreground=dark_fg, fieldbackground=dark_bg)
    style.configure("Treeview.Heading", background=button_bg, foreground=dark_fg)

    # Update the root window background
    root.configure(bg=dark_bg)

    # Update schedule_canvas background if it exists
    try:
        schedule_canvas.configure(bg="#181818")
    except Exception:
        pass

def update_fonts_and_colors():
    default_font = ("Roboto", 10)
    header_font = ("Roboto", 12, "bold")

    # Apply fonts to widgets
    root.option_add("*Font", default_font)
    root.option_add("*TLabel.Font", header_font)
    root.option_add("*TButton.Font", default_font)

def toggle_view_mode():
    current_mode = view_mode_var.get()
    if current_mode == "Daily":
        view_mode_var.set("Weekly")
    elif current_mode == "Weekly":
        view_mode_var.set("Monthly")
    else:
        view_mode_var.set("Daily")
    print(f"View mode changed to: {view_mode_var.get()}")  # Debugging statement
    fetch_events()  # Refresh the schedule with the new view mode

# Part 4: Schedule and Event Management
def create_schedule_view(schedule_frame):
    global schedule_canvas

    # Theme-aware background color
    canvas_bg = "#181818" if theme_mode == "dark" else "#ffffff"

    # Create the schedule canvas
    schedule_canvas = tk.Canvas(schedule_frame, bg=canvas_bg, scrollregion=(0, 0, 3000, 1500))
    schedule_canvas.grid(row=0, column=0, sticky="nsew")  # Make the canvas fill the frame

    # Add horizontal and vertical scrollbars
    h_scroll = tk.Scrollbar(schedule_frame, orient="horizontal", command=schedule_canvas.xview)
    h_scroll.grid(row=1, column=0, sticky="ew")
    v_scroll = tk.Scrollbar(schedule_frame, orient="vertical", command=schedule_canvas.yview)
    v_scroll.grid(row=0, column=1, sticky="ns")
    schedule_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    # Configure the parent frame to allow resizing
    schedule_frame.grid_rowconfigure(0, weight=1)  # Allow the canvas to expand vertically
    schedule_frame.grid_columnconfigure(0, weight=1)  # Allow the canvas to expand horizontally

    # Debugging: Print layout configuration
    print("Schedule frame layout configured with grid_rowconfigure and grid_columnconfigure.")

# ...inside open_add_event_window()...

def open_add_event_window():
    def add_event():
        # Collect data from the fields
        event_name = event_name_entry.get().strip()
        event_date = calendar.get_date()
        description = description_entry.get("1.0", tk.END).strip()
        event_color = color_var.get()
        selected_employee_name = employee_var.get()
        selected_client_name = client_var.get()

        # Validate time inputs for start and end times
        try:
            start_hour = int(start_hour_entry.get())
            start_minute = int(start_minute_entry.get())
            end_hour = int(end_hour_entry.get())
            end_minute = int(end_minute_entry.get())

            # Convert to 24-hour format based on AM/PM selection
            if start_am_pm_var.get() == "PM" and start_hour != 12:
                start_hour += 12
            elif start_am_pm_var.get() == "AM" and start_hour == 12:
                start_hour = 0

            if end_am_pm_var.get() == "PM" and end_hour != 12:
                end_hour += 12
            elif end_am_pm_var.get() == "AM" and end_hour == 12:
                end_hour = 0

            event_start_time = time(start_hour, start_minute)
            event_end_time = time(end_hour, end_minute)

            if event_start_time >= event_end_time:
                messagebox.showwarning("Input Error", "End time must be after start time.")
                return
        except ValueError as e:
            messagebox.showwarning("Input Error", f"Invalid time input: {e}")
            return

        # Validate employee selection
        if not selected_employee_name or selected_employee_name == "Select Employee":
            messagebox.showwarning("Input Error", "Please select an employee.")
            return

        # Validate client selection
        if not selected_client_name or selected_client_name == "Select Client":
            messagebox.showwarning("Input Error", "Please select a client.")
            return

        # Extract EmployeeID from the employees dictionary
        employees = fetch_employee_names()
        selected_employee_id = None
        for emp_id, emp_name in employees.items():
            if emp_name == selected_employee_name:
                selected_employee_id = emp_id
                break

        if selected_employee_id is None:
            messagebox.showwarning("Input Error", "Invalid employee selection.")
            return

        # Extract ClientID from the clients dictionary
        clients = fetch_client_names()
        selected_client_id = None
        for cid, cname in clients.items():
            if cname == selected_client_name:
                selected_client_id = cid
                break

        if selected_client_id is None:
            messagebox.showwarning("Input Error", "Invalid client selection.")
            return

        # Validate required fields
        if not event_name or not event_date:
            messagebox.showwarning("Input Error", "Please fill in all required fields.")
            return

        # --- Recurring event logic ---
        if is_recurring_var.get():
            pattern = pattern_var.get()
            try:
                interval = int(interval_entry.get())
            except ValueError:
                messagebox.showwarning("Input Error", "Interval must be a number.")
                return
            end_date_str = end_date_entry.get().strip()
            end_date = end_date_str if end_date_str else None

            try:
                connection = connect_to_database()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute('''
                        INSERT INTO RecurringEvents (Pattern, `Interval`, StartDate, EndDate, EventName, Description, EventColor, EmployeeID, ClientID, StartTime, EndTime)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pattern, interval, event_date, end_date, event_name, description, event_color, selected_employee_id, selected_client_id, event_start_time, event_end_time
                    ))
                    recurring_id = cursor.lastrowid

                    # Generate event dates
                    from datetime import timedelta
                    dt_start = datetime.strptime(event_date, "%Y-%m-%d")
                    if end_date:
                        dt_end = datetime.strptime(end_date, "%Y-%m-%d")
                    else:
                        dt_end = dt_start + timedelta(days=365*2)  # Default: 2 years

                    dates = []
                    dt = dt_start
                    while dt <= dt_end:
                        dates.append(dt.strftime("%Y-%m-%d"))
                        if pattern == "daily":
                            dt += timedelta(days=interval)
                        elif pattern == "weekly":
                            dt += timedelta(weeks=interval)
                        elif pattern == "biweekly":
                            dt += timedelta(weeks=2*interval)
                        elif pattern == "monthly":
                            month = dt.month - 1 + interval
                            year = dt.year + month // 12
                            month = month % 12 + 1
                            day = min(dt.day, [31,
                                29 if year%4==0 and (year%100!=0 or year%400==0) else 28,
                                31,30,31,30,31,31,30,31,30,31][month-1])
                            dt = dt.replace(year=year, month=month, day=day)
                        elif pattern == "yearly":
                            try:
                                dt = dt.replace(year=dt.year + interval)
                            except ValueError:
                                dt = dt.replace(month=2, day=28, year=dt.year + interval)
                        else:
                            break

                    # Insert all events
                    for d in dates:
                        cursor.execute('''
                            INSERT INTO Events (EventName, EventDate, EventStartTime, EventEndTime, Description, EventColor, EmployeeID, ClientID, RecurringID)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (event_name, d, event_start_time, event_end_time, description, event_color, selected_employee_id, selected_client_id, recurring_id))
                    connection.commit()
                    connection.close()
                    messagebox.showinfo("Success", "Recurring events added successfully!")
                    add_event_window.destroy()
                    fetch_events()
            except Exception as e:
                print("Error adding recurring event:", e)
                traceback.print_exc()
                messagebox.showerror("Database Error", f"Error adding recurring event: {e}")
            return

        # --- Non-recurring event logic ---
        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO Events (EventName, EventDate, EventStartTime, EventEndTime, Description, EventColor, EmployeeID, ClientID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event_name, event_date, event_start_time, event_end_time, description, event_color, selected_employee_id, selected_client_id))
                connection.commit()
                connection.close()
                messagebox.showinfo("Success", "Event added successfully!")
                add_event_window.destroy()
                fetch_events()  # Refresh the schedule view
        except Exception as e:
            print("Error adding event:", e)
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error adding event: {e}")

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    # Create a pop-up window for adding an event
    add_event_window = tk.Toplevel(root)
    add_event_window.title("Add Event")
    add_event_window.geometry("600x650")
    add_event_window.configure(bg=bg_color)

    # Recurring event checkbox and options
    is_recurring_var = tk.BooleanVar(value=False)
    recurring_frame = tk.Frame(add_event_window, bg=bg_color)
    recurring_frame.grid(row=10, column=0, columnspan=2, pady=5, sticky="w")

    def toggle_recurring_options():
        if is_recurring_var.get():
            recurring_options_frame.grid(row=11, column=0, columnspan=2, sticky="w", padx=10)
        else:
            recurring_options_frame.grid_remove()

    tk.Checkbutton(
        recurring_frame, text="Recurring Event", variable=is_recurring_var,
        command=toggle_recurring_options, bg=bg_color, fg=fg_color, selectcolor=entry_bg
    ).pack(side="left")

    recurring_options_frame = tk.Frame(add_event_window, bg=bg_color)
    tk.Label(recurring_options_frame, text="Repeat:", bg=bg_color, fg=fg_color).grid(row=0, column=0, sticky="e")
    pattern_var = tk.StringVar(value="weekly")
    pattern_menu = ttk.Combobox(recurring_options_frame, textvariable=pattern_var, values=["daily", "weekly", "biweekly", "monthly", "yearly"], state="readonly")
    pattern_menu.grid(row=0, column=1, padx=5)
    tk.Label(recurring_options_frame, text="Every", bg=bg_color, fg=fg_color).grid(row=0, column=2, sticky="e")
    interval_entry = tk.Entry(recurring_options_frame, width=3)
    interval_entry.insert(0, "1")
    interval_entry.grid(row=0, column=3, padx=5)
    tk.Label(recurring_options_frame, text="End Date (optional):", bg=bg_color, fg=fg_color).grid(row=1, column=0, sticky="e")
    end_date_entry = tk.Entry(recurring_options_frame, width=12)
    end_date_entry.grid(row=1, column=1, padx=5)
    recurring_options_frame.grid_remove()

    # Event Name
    tk.Label(add_event_window, text="Event Name:", bg=bg_color, fg=fg_color).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    event_name_entry = tk.Entry(add_event_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    event_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

    # Event Date
    tk.Label(add_event_window, text="Event Date:", bg=bg_color, fg=fg_color).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    event_date_label = tk.Label(add_event_window, text=calendar.get_date(), bg=bg_color, fg=fg_color)
    event_date_label.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # Description
    tk.Label(add_event_window, text="Description:", bg=bg_color, fg=fg_color).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    description_entry = tk.Text(add_event_window, height=3, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    description_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    # Event Color
    tk.Label(add_event_window, text="Event Color:", bg=bg_color, fg=fg_color).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    color_var = tk.StringVar(value="blue")
    color_options = ["blue", "red", "green", "yellow", "purple"]
    color_menu = tk.OptionMenu(add_event_window, color_var, *color_options)
    color_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    color_menu.grid(row=3, column=1, padx=10, pady=5, sticky="w")

    # Select Employee
    tk.Label(add_event_window, text="Select Employee:", bg=bg_color, fg=fg_color).grid(row=4, column=0, padx=10, pady=5, sticky="e")
    employee_var = tk.StringVar(value="Select Employee")
    employees = fetch_employee_names()
    employee_menu = tk.OptionMenu(add_event_window, employee_var, *employees.values())
    employee_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    employee_menu.grid(row=4, column=1, padx=10, pady=5, sticky="w")

    # Select Client
    tk.Label(add_event_window, text="Select Client:", bg=bg_color, fg=fg_color).grid(row=5, column=0, padx=10, pady=5, sticky="e")
    client_var = tk.StringVar(value="Select Client")
    clients = fetch_client_names()
    client_menu = tk.OptionMenu(add_event_window, client_var, *clients.values())
    client_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    client_menu.grid(row=5, column=1, padx=10, pady=5, sticky="w")

    # Start Time
    tk.Label(add_event_window, text="Start Time:", bg=bg_color, fg=fg_color).grid(row=6, column=0, padx=10, pady=5, sticky="e")
    start_time_frame = tk.Frame(add_event_window, bg=bg_color)
    start_time_frame.grid(row=6, column=1, padx=10, pady=5, sticky="w")
    start_hour_entry = tk.Entry(start_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    start_hour_entry.pack(side="left")
    tk.Label(start_time_frame, text=":", bg=bg_color, fg=fg_color).pack(side="left")
    start_minute_entry = tk.Entry(start_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    start_minute_entry.pack(side="left")
    start_am_pm_var = tk.StringVar(value="AM")
    tk.Radiobutton(start_time_frame, text="AM", variable=start_am_pm_var, value="AM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")
    tk.Radiobutton(start_time_frame, text="PM", variable=start_am_pm_var, value="PM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")

    # End Time
    tk.Label(add_event_window, text="End Time:", bg=bg_color, fg=fg_color).grid(row=7, column=0, padx=10, pady=5, sticky="e")
    end_time_frame = tk.Frame(add_event_window, bg=bg_color)
    end_time_frame.grid(row=7, column=1, padx=10, pady=5, sticky="w")
    end_hour_entry = tk.Entry(end_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    end_hour_entry.pack(side="left")
    tk.Label(end_time_frame, text=":", bg=bg_color, fg=fg_color).pack(side="left")
    end_minute_entry = tk.Entry(end_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    end_minute_entry.pack(side="left")
    end_am_pm_var = tk.StringVar(value="AM")
    tk.Radiobutton(end_time_frame, text="AM", variable=end_am_pm_var, value="AM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")
    tk.Radiobutton(end_time_frame, text="PM", variable=end_am_pm_var, value="PM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")

    # Save and Cancel Buttons
    tk.Button(add_event_window, text="Save", command=add_event, bg=entry_bg, fg=entry_fg).grid(row=8, column=0, pady=20)
    tk.Button(add_event_window, text="Cancel", command=add_event_window.destroy, bg=entry_bg, fg=entry_fg).grid(row=8, column=1, pady=20)

# Create the sidebar
def create_sidebar():
    global calendar
    sidebar = ttk.Frame(root, width=200)
    sidebar.grid(row=1, column=0, sticky="ns", padx=10, pady=10)

    # Add the calendar to the sidebar
    calendar_label = ttk.Label(sidebar, text="Select Date:")
    calendar_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    calendar = Calendar(sidebar, date_pattern="yyyy-mm-dd", selectmode="day")
    calendar.grid(row=1, column=0, padx=5, pady=5, sticky="w")
    calendar.bind("<<CalendarSelected>>", lambda event: fetch_events())

def open_update_event_window(event_data):
    if not event_data:
        messagebox.showerror("Error", "No event selected for updating.")
        return

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    def update_event():
        event_name = event_name_entry.get().strip()
        event_date = calendar.get_date()
        description = description_entry.get("1.0", tk.END).strip()
        event_color = color_var.get()
        selected_employee = employee_var.get()
        selected_client = client_var.get()

        # Validate time inputs
        try:
            start_hour = int(start_hour_entry.get())
            start_minute = int(start_minute_entry.get())
            end_hour = int(end_hour_entry.get())
            end_minute = int(end_minute_entry.get())

            if start_am_pm_var.get() == "PM" and start_hour != 12:
                start_hour += 12
            elif start_am_pm_var.get() == "AM" and start_hour == 12:
                start_hour = 0

            if end_am_pm_var.get() == "PM" and end_hour != 12:
                end_hour += 12
            elif end_am_pm_var.get() == "AM" and end_hour == 12:
                end_hour = 0

            event_start_time = time(start_hour, start_minute)
            event_end_time = time(end_hour, end_minute)

            if event_start_time >= event_end_time:
                messagebox.showwarning("Input Error", "End time must be after start time.")
                return
        except ValueError as e:
            messagebox.showwarning("Input Error", f"Invalid time input: {e}")
            return

        # Validate employee selection
        if not selected_employee or selected_employee == "Select Employee":
            messagebox.showwarning("Input Error", "Please select an employee.")
            return

        # Validate client selection
        if not selected_client or selected_client == "Select Client":
            messagebox.showwarning("Input Error", "Please select a client.")
            return

        # Extract EmployeeID from the employees dictionary
        employees_dict = fetch_employee_names()
        selected_employee_id = None
        for emp_id, emp_name in employees_dict.items():
            if emp_name == selected_employee:
                selected_employee_id = emp_id
                break
        if selected_employee_id is None:
            messagebox.showwarning("Input Error", "Invalid employee selection.")
            return

        # Extract ClientID from the clients dictionary
        clients_dict = fetch_client_names()
        selected_client_id = None
        for cid, cname in clients_dict.items():
            if cname == selected_client:
                selected_client_id = cid
                break
        if selected_client_id is None:
            messagebox.showwarning("Input Error", "Invalid client selection.")
            return

        # Update the event in the database
        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                cursor.execute('''
                    UPDATE Events
                    SET EventName = ?, EventDate = ?, EventStartTime = ?, EventEndTime = ?, Description = ?, EventColor = ?, EmployeeID = ?, ClientID = ?
                    WHERE EventName = ? AND EventDate = ? AND EventStartTime = ?
                ''', (event_name, event_date, event_start_time, event_end_time, description, event_color, selected_employee_id, selected_client_id,
                      event_data["name"], event_data["date"], event_data["time"]))
                connection.commit()
                connection.close()
                messagebox.showinfo("Success", "Event updated successfully!")
                update_event_window.destroy()
                fetch_events()  # Refresh the schedule view
        except Exception as e:
            print("Error updating event:", e)
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error updating event: {e}")

    # Create the pop-up window
    update_event_window = tk.Toplevel(root)
    update_event_window.title("Update Event")
    update_event_window.geometry("600x450")
    update_event_window.configure(bg=bg_color)

    # Pre-fill fields with event data
    tk.Label(update_event_window, text="Event Name:", bg=bg_color, fg=fg_color).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    event_name_entry = tk.Entry(update_event_window, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    event_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
    event_name_entry.insert(0, event_data["name"])

    tk.Label(update_event_window, text="Event Date:", bg=bg_color, fg=fg_color).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    tk.Label(update_event_window, text=event_data["date"], bg=bg_color, fg=fg_color).grid(row=1, column=1, padx=10, pady=5, sticky="w")

    # Description
    tk.Label(update_event_window, text="Description:", bg=bg_color, fg=fg_color).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    description_entry = tk.Text(update_event_window, height=3, width=30, bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    description_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    description_entry.insert("1.0", event_data.get("description", ""))

    # Event Color
    tk.Label(update_event_window, text="Event Color:", bg=bg_color, fg=fg_color).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    color_var = tk.StringVar(value=event_data.get("color", "blue"))
    color_options = ["blue", "red", "green", "yellow", "purple"]
    color_menu = tk.OptionMenu(update_event_window, color_var, *color_options)
    color_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    color_menu.grid(row=3, column=1, padx=10, pady=5, sticky="w")

    # Select Employee
    tk.Label(update_event_window, text="Select Employee:", bg=bg_color, fg=fg_color).grid(row=4, column=0, padx=10, pady=5, sticky="e")
    employee_var = tk.StringVar(value="Select Employee")
    employees = fetch_employee_names()
    employee_menu = tk.OptionMenu(update_event_window, employee_var, *employees.values())
    employee_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    employee_menu.grid(row=4, column=1, padx=10, pady=5, sticky="w")
    for emp_id, emp_name in employees.items():
        if emp_id == event_data.get("employee_id"):
            employee_var.set(emp_name)
            break

    # Select Client
    tk.Label(update_event_window, text="Select Client:", bg=bg_color, fg=fg_color).grid(row=5, column=0, padx=10, pady=5, sticky="e")
    client_var = tk.StringVar(value="Select Client")
    clients = fetch_client_names()
    client_menu = tk.OptionMenu(update_event_window, client_var, *clients.values())
    client_menu.configure(bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    client_menu.grid(row=5, column=1, padx=10, pady=5, sticky="w")
    # Optionally pre-select the client if you want:
    for cid, cname in clients.items():
        if cid == event_data.get("client_id"):
            client_var.set(cname)
            break

    # Start Time
    tk.Label(update_event_window, text="Start Time:", bg=bg_color, fg=fg_color).grid(row=6, column=0, padx=10, pady=5, sticky="e")
    start_time_frame = tk.Frame(update_event_window, bg=bg_color)
    start_time_frame.grid(row=6, column=1, padx=10, pady=5, sticky="w")
    start_hour_entry = tk.Entry(start_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    start_hour_entry.pack(side="left")
    tk.Label(start_time_frame, text=":", bg=bg_color, fg=fg_color).pack(side="left")
    start_minute_entry = tk.Entry(start_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    start_minute_entry.pack(side="left")
    start_am_pm_var = tk.StringVar(value="AM")
    tk.Radiobutton(start_time_frame, text="AM", variable=start_am_pm_var, value="AM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")
    tk.Radiobutton(start_time_frame, text="PM", variable=start_am_pm_var, value="PM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")

    # End Time
    tk.Label(update_event_window, text="End Time:", bg=bg_color, fg=fg_color).grid(row=7, column=0, padx=10, pady=5, sticky="e")
    end_time_frame = tk.Frame(update_event_window, bg=bg_color)
    end_time_frame.grid(row=7, column=1, padx=10, pady=5, sticky="w")
    end_hour_entry = tk.Entry(end_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    end_hour_entry.pack(side="left")
    tk.Label(end_time_frame, text=":", bg=bg_color, fg=fg_color).pack(side="left")
    end_minute_entry = tk.Entry(end_time_frame, width=2, justify="center", bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)
    end_minute_entry.pack(side="left")
    end_am_pm_var = tk.StringVar(value="AM")
    tk.Radiobutton(end_time_frame, text="AM", variable=end_am_pm_var, value="AM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")
    tk.Radiobutton(end_time_frame, text="PM", variable=end_am_pm_var, value="PM", bg=bg_color, fg=fg_color, selectcolor=entry_bg).pack(side="left")

    # Add update button
    tk.Button(update_event_window, text="Update Event", command=update_event, bg=entry_bg, fg=entry_fg).grid(row=8, column=0, columnspan=2, pady=10)

def open_update_event_selection_window():
    global current_start_date, current_end_date

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    # Create a pop-up window for selecting an event to update
    update_event_window = tk.Toplevel(root)
    update_event_window.title(f"Update Events from {current_start_date} to {current_end_date}")
    update_event_window.geometry("400x400")
    update_event_window.configure(bg=bg_color)

    tk.Label(update_event_window, text=f"Events from {current_start_date} to {current_end_date}:", bg=bg_color, fg=fg_color).grid(pady=10)

    # Listbox to display events
    event_listbox = tk.Listbox(update_event_window, selectmode="single", width=50, height=15, bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    event_listbox.grid(pady=10)

    # Fetch events for the selected date range
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT EventName, EventDate, EventStartTime, EventEndTime, Description, EventColor, EmployeeID FROM Events WHERE EventDate BETWEEN ? AND ?', (current_start_date, current_end_date))
            events = cursor.fetchall()
            connection.close()

            # Populate the Listbox with events
            for event in events:
                event_name, event_date, event_start_time, event_end_time, description, event_color, employee_id = event
                event_listbox.insert(tk.END, f"{event_name} on {event_date} from {event_start_time} to {event_end_time}")
    except Exception as e:
        print("Error fetching events:", e)
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error fetching events: {e}")
        update_event_window.destroy()
        return

    def update_selected_event():
        selected_index = event_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("No Selection", "Please select an event to update.")
            return

        try:
            # Extract event details from the selected item
            event_text = event_listbox.get(selected_index[0])
            event_name, event_date, event_time_range = event_text.split(" on ")[0], event_text.split(" on ")[1].split(" from ")[0], event_text.split(" from ")[1]
            event_start_time, event_end_time = event_time_range.split(" to ")

            # Fetch full event details from the database
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT EventName, EventDate, EventStartTime, EventEndTime, Description, EventColor, EmployeeID
                    FROM Events
                    WHERE EventName = ? AND EventDate = ? AND EventStartTime = ?
                ''', (event_name, event_date, event_start_time))
                event = cursor.fetchone()
                connection.close()

                if event:
                    event_data = {
                        "name": event[0],
                        "date": event[1],
                        "time": event[2],
                        "end_time": event[3],
                        "description": event[4],
                        "color": event[5],
                        "employee_id": event[6],
                    }
                    update_event_window.destroy()
                    open_update_event_window(event_data)
                else:
                    messagebox.showerror("Error", "Could not find event details.")
        except Exception as e:
            print("Error processing selected event:", e)
            traceback.print_exc()
            messagebox.showerror("Error", f"Error processing selected event: {e}")

    # Buttons for updating or canceling
    tk.Button(update_event_window, text="Update Selected", command=update_selected_event, bg=entry_bg, fg=entry_fg).grid(pady=10)
    tk.Button(update_event_window, text="Cancel", command=update_event_window.destroy, bg=entry_bg, fg=entry_fg).grid(pady=10)

def delete_selected_event():
    global current_start_date, current_end_date

    print(f"Fetching events for range: {current_start_date} to {current_end_date}")  # Debugging statement

    # Theme-aware colors
    bg_color = "#121212" if theme_mode == "dark" else "#ffffff"
    fg_color = "#ffffff" if theme_mode == "dark" else "#000000"
    entry_bg = "#333333" if theme_mode == "dark" else "#f0f0f0"
    entry_fg = "#ffffff" if theme_mode == "dark" else "#000000"

    # Create a pop-up window for selecting events to delete
    delete_event_window = tk.Toplevel(root)
    delete_event_window.title(f"Delete Events from {current_start_date} to {current_end_date}")
    delete_event_window.geometry("450x450")
    delete_event_window.configure(bg=bg_color)

    tk.Label(delete_event_window, text=f"Events from {current_start_date} to {current_end_date}:", bg=bg_color, fg=fg_color).grid(pady=10)

    # Listbox to display events
    event_listbox = tk.Listbox(delete_event_window, selectmode="multiple", width=50, height=15, bg=entry_bg, fg=entry_fg, highlightbackground=bg_color)
    event_listbox.grid(pady=10, padx=25)

    # Fetch events for the selected date range
    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('SELECT EventName, EventDate, EventStartTime, EventEndTime FROM Events WHERE EventDate BETWEEN ? AND ?', (current_start_date, current_end_date))
            events = cursor.fetchall()
            connection.close()

            # Populate the Listbox with events
            for event in events:
                event_name, event_date, event_start_time, event_end_time = event
                event_listbox.insert(tk.END, f"{event_name} on {event_date} from {event_start_time} to {event_end_time}")
    except Exception as e:
        print("Error fetching events:", e)  # Debugging statement
        traceback.print_exc()
        messagebox.showerror("Database Error", f"Error fetching events: {e}")
        delete_event_window.destroy()
        return

    def delete_selected():
        # Get selected items from the Listbox
        selected_indices = event_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one event to delete.")
            return

        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                for index in selected_indices:
                    event_text = event_listbox.get(index)
                    event_name, event_date, event_time_range = event_text.split(" on ")[0], event_text.split(" on ")[1].split(" from ")[0], event_text.split(" from ")[1]
                    event_start_time, event_end_time = event_time_range.split(" to ")

                    print(f"Deleting event: {event_name}, {event_date}, {event_start_time} to {event_end_time}")  # Debugging statement

                    # Execute DELETE query
                    cursor.execute('''
                        DELETE FROM Events 
                        WHERE EventName = ? AND EventDate = ? AND EventStartTime = ? AND EventEndTime = ?
                    ''', (event_name, event_date, event_start_time, event_end_time))
                connection.commit()
                connection.close()

                # Refresh the schedule view
                fetch_events()
                messagebox.showinfo("Success", "Selected events have been deleted.")
                delete_event_window.destroy()
        except Exception as e:
            print("Error deleting events:", e)  # Debugging statement
            traceback.print_exc()
            messagebox.showerror("Database Error", f"Error deleting events: {e}")

            # --- Add the Delete button ---
    delete_btn = tk.Button(delete_event_window, text="Delete Selected", command=delete_selected, bg="#e53935", fg="#fff")
    delete_btn.grid(pady=10)

def update_selected_event(event_listbox, update_event_window):
        # Get the selected item from the Listbox
        selected_index = event_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("No Selection", "Please select an event to update.")
            return

        try:
            # Extract event details from the selected item
            event_text = event_listbox.get(selected_index[0])
            event_name, event_date, event_time_range = event_text.split(" on ")[0], event_text.split(" on ")[1].split(" from ")[0], event_text.split(" from ")[1]
            event_start_time, event_end_time = event_time_range.split(" to ")

            # Open the update event window with the selected event's details
            event_data = {
                "name": event_name,
                "date": event_date,
                "time": event_start_time,
                "end_time": event_end_time,
            }
            update_event_window.destroy()  # Close the selection window
            open_update_event_window(event_data)
        except Exception as e:
            print("Error processing selected event:", e)  # Debugging statement
            traceback.print_exc()
            messagebox.showerror("Error", f"Error processing selected event: {e}")

def auto_refresh():
    """
    Automatically refreshes the schedule view at regular intervals.
    """
    fetch_events()  # Refresh the schedule view
    root.after(60000, auto_refresh)  # Refresh every 60 seconds

# Create the top toolbar
def clear_default_sender_data():
    if messagebox.askyesno("Confirm", "Are you sure you want to delete all default sender email and password data?"):
        try:
            connection = connect_to_database()
            if connection:
                cursor = connection.cursor()
                # Remove all default sender flags and passwords
                cursor.execute("UPDATE Employees SET IsDefaultSender=0, EmailPassword=NULL")
                connection.commit()
                connection.close()
                messagebox.showinfo("Success", "All default sender email and password data deleted.")
        except Exception as e:
            print("Error clearing default sender data:", e)
            messagebox.showerror("Database Error", f"Error clearing default sender data: {e}")

def create_top_toolbar():
    top_toolbar = ttk.Frame(root)
    top_toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

    # Add a dropdown for view selection
    view_mode_label = ttk.Label(top_toolbar, text="View Mode:")
    view_mode_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

    view_mode_dropdown = ttk.Combobox(top_toolbar, textvariable=view_mode_var, values=["Daily", "Weekly", "Monthly"], state="readonly")
    view_mode_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    view_mode_dropdown.bind("<<ComboboxSelected>>", lambda event: fetch_events())

    # Add toolbar buttons
    ttk.Button(top_toolbar, text="Add Event", command=open_add_event_window).grid(row=0, column=2, padx=5, pady=5)
    ttk.Button(top_toolbar, text="Delete Selected Event", command=delete_selected_event).grid(row=0, column=3, padx=5, pady=5)
    ttk.Button(top_toolbar, text="Update Event", command=open_update_event_selection_window).grid(row=0, column=4, padx=5, pady=5)
    ttk.Button(top_toolbar, text="Manage Recurring Events", command=open_manage_recurring_events_window).grid(row=0, column=5, padx=5, pady=5)
    ttk.Button(top_toolbar, text="Send Event Emails (Today)", command=send_event_complete_emails_for_today).grid(row=0, column=8, padx=5, pady=5)
    theme_var = tk.StringVar(value="Dark" if theme_mode == "dark" else "Light")
    def on_theme_change(event=None):
        global theme_mode
        if theme_var.get() == "Dark":
            theme_mode = "dark"
            apply_dark_theme()
        else:
            theme_mode = "light"
            apply_light_theme()
        update_fonts_and_colors()
        fetch_events()  # Redraw schedule with new theme

    # Place the theme dropdown at the far right
    theme_dropdown = ttk.Combobox(top_toolbar, textvariable=theme_var, values=["Dark", "Light"], state="readonly", width=8)
    theme_dropdown.grid(row=0, column=99, padx=5, pady=5, sticky="e")
    theme_dropdown.bind("<<ComboboxSelected>>", on_theme_change)
    top_toolbar.grid_columnconfigure(98, weight=1)

def create_notebook():
    global main_notebook, schedule_tab, employees_tab, clients_tab

    main_notebook = ttk.Notebook(root)
    main_notebook.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

    schedule_tab = ttk.Frame(main_notebook)
    main_notebook.add(schedule_tab, text="Schedule")

    employees_tab = ttk.Frame(main_notebook)
    main_notebook.add(employees_tab, text="Employees List")

    clients_tab = ttk.Frame(main_notebook)
    main_notebook.add(clients_tab, text="Clients List")

    # Make notebook expand to fill root
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)
    main_notebook.grid_rowconfigure(0, weight=1)
    main_notebook.grid_columnconfigure(0, weight=1)

    # Make schedule tab expand to fill notebook
    schedule_tab.grid_rowconfigure(0, weight=1)
    schedule_tab.grid_columnconfigure(0, weight=1)

    # Add the schedule frame to the Schedule tab
    schedule_frame = tk.Frame(schedule_tab)
    schedule_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # Make schedule frame expand to fill schedule tab
    schedule_frame.grid_rowconfigure(0, weight=1)
    schedule_frame.grid_columnconfigure(0, weight=1)

    # Initialize the schedule canvas
    create_schedule_view(schedule_frame)

    # Add the employee management UI to the Employees tab
    create_employees_tab(employees_tab)

    create_clients_tab(clients_tab)

    # Debugging: Print layout configuration
    print("Notebook and parent containers configured with grid_rowconfigure and grid_columnconfigure.")

def create_schedule_view(schedule_frame):
    global schedule_canvas

    # Create the schedule canvas
    schedule_canvas = tk.Canvas(schedule_frame, bg="white", scrollregion=(0, 0, 3000, 1500))
    schedule_canvas.grid(row=0, column=0, sticky="nsew")  # Make the canvas fill the frame

    # Add horizontal and vertical scrollbars
    h_scroll = tk.Scrollbar(schedule_frame, orient="horizontal", command=schedule_canvas.xview)
    h_scroll.grid(row=1, column=0, sticky="ew")
    v_scroll = tk.Scrollbar(schedule_frame, orient="vertical", command=schedule_canvas.yview)
    v_scroll.grid(row=0, column=1, sticky="ns")
    schedule_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    # Configure the parent frame to allow resizing
    schedule_frame.grid_rowconfigure(0, weight=1)  # Allow the canvas to expand vertically
    schedule_frame.grid_columnconfigure(0, weight=1)  # Allow the canvas to expand horizontally

    # Debugging: Print layout configuration
    print("Schedule frame layout configured with grid_rowconfigure and grid_columnconfigure.")

def draw_grid(start_date, end_date, employees, view_mode):
    schedule_canvas.delete("all")
    # Sizing for each view
    daily_weekly_row_height = 50
    daily_weekly_col_width = 150
    monthly_row_height = 100
    monthly_col_width = 180

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    # Theme-aware colors
    if theme_mode == "dark":
        header_bg = "#1e88e5"
        cell_bg = "#181818"
        cell_fg = "#fff"
        cell_border = "#333"
        empty_bg = "#111"
        empty_border = "#222"
    else:
        header_bg = "#1e88e5"
        cell_bg = "#fff"
        cell_fg = "#000"
        cell_border = "#bbb"
        empty_bg = "#f0f0f0"
        empty_border = "#e0e0e0"

    # ...rest of your function...

    if view_mode in ["Daily", "Weekly"]:
        row_height = daily_weekly_row_height
        col_width = daily_weekly_col_width

        # Draw the header row (dates) at the top
        if view_mode == "Daily":
            schedule_canvas.create_rectangle(col_width, 0, col_width * 2, row_height, fill=header_bg, outline="white")
            schedule_canvas.create_text(col_width + col_width / 2, row_height / 2, text=start_date, fill="white", font=("Roboto", 10, "bold"))
        elif view_mode == "Weekly":
            date_list = [(start_date_obj + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            for col, date in enumerate(date_list):
                x = col * col_width + col_width
                schedule_canvas.create_rectangle(x, 0, x + col_width, row_height, fill=header_bg, outline="white")
                schedule_canvas.create_text(x + col_width / 2, row_height / 2, text=date, fill="white", font=("Roboto", 10, "bold"))

        # Draw time slots on the left side, starting from row 1
        for row in range(24):
            y = (row + 1) * row_height
            time_label = f"{row:02d}:00"
            schedule_canvas.create_rectangle(0, y, col_width, y + row_height, fill="#333333", outline="white")
            schedule_canvas.create_text(col_width / 2, y + row_height / 2, text=time_label, fill="white", font=("Roboto", 10))

        # Draw the grid cells for each hour
        if view_mode == "Daily":
            for row in range(24):
                y = (row + 1) * row_height
                schedule_canvas.create_rectangle(col_width, y, col_width * 2, y + row_height, outline="white")
        elif view_mode == "Weekly":
            for row in range(24):
                y = (row + 1) * row_height
                for col in range(7):
                    x = col * col_width + col_width
                    schedule_canvas.create_rectangle(x, y, x + col_width, y + row_height, outline="white")

    elif view_mode == "Monthly":
        row_height = monthly_row_height
        col_width = monthly_col_width

        # Calculate the first day of the month and which weekday it is
        first_day = start_date_obj.replace(day=1)
        first_weekday = first_day.weekday()  # Monday=0
        # Calculate days in month robustly
        next_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
        days_in_month = (next_month - timedelta(days=1)).day
        total_cells = first_weekday + days_in_month
        num_rows = (total_cells + 6) // 7

        # Draw weekday headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, wd in enumerate(weekdays):
            x1 = col * col_width
            x2 = x1 + col_width
            schedule_canvas.create_rectangle(x1, 0, x2, row_height, fill=header_bg, outline="white")
            schedule_canvas.create_text((x1 + x2) / 2, row_height / 2, text=wd, fill="white", font=("Roboto", 10, "bold"))

        # Draw day cells
        day = 1
        for row in range(num_rows):
            for col in range(7):
                cell_idx = row * 7 + col
                x1 = col * col_width
                y1 = (row + 1) * row_height
                x2 = x1 + col_width
                y2 = y1 + row_height
                if cell_idx >= first_weekday and day <= days_in_month:
                    schedule_canvas.create_rectangle(x1, y1, x2, y2, fill=cell_bg, outline=cell_border)
                    schedule_canvas.create_text(x1 + 10, y1 + 10, text=str(day), anchor="nw", fill=cell_fg, font=("Roboto", 10, "bold"), width=col_width-24)
                    day += 1
                else:
                    schedule_canvas.create_rectangle(x1, y1, x2, y2, fill=empty_bg, outline=empty_border)

    schedule_canvas.configure(scrollregion=schedule_canvas.bbox("all"))
    schedule_canvas.update_idletasks()

def get_overlapping_groups(events):
    """
    Groups overlapping events together for a single day.
    Returns a list of lists, where each sublist is a group of overlapping events.
    """
    # Sort events by start time
    events = sorted(events, key=lambda e: e[2])  # e[2] is start_time
    groups = []
    current_group = []

    for event in events:
        if not current_group:
            current_group.append(event)
        else:
            last_end = current_group[-1][3]  # e[3] is end_time
            if event[2] < last_end:  # Overlaps
                current_group.append(event)
            else:
                groups.append(current_group)
                current_group = [event]
    if current_group:
        groups.append(current_group)
    return groups

def timedelta_to_str(td):
    """Convert a timedelta object to HH:MM:SS string."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def draw_events(events, start_date, employees, view_mode):
    daily_weekly_row_height = 50
    daily_weekly_col_width = 150
    monthly_row_height = 100
    monthly_col_width = 180

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")

    # Theme-aware colors
    if theme_mode == "dark":
        cell_fg = "#fff"
        popup_bg = "#232323"
        popup_fg = "#fff"
    else:
        cell_fg = "#000"
        popup_bg = "#f8f8f8"
        popup_fg = "#000"

    # Helper: show popup
    def show_event_popup(event_data, x, y):
        if hasattr(draw_events, "popup") and draw_events.popup:
            try:
                draw_events.popup.destroy()
            except Exception:
                pass
        popup = tk.Toplevel(root)
        draw_events.popup = popup
        popup.overrideredirect(True)
        popup.geometry(f"+{x}+{y}")
        popup.configure(bg=popup_bg)
        fg = popup_fg
        tk.Label(popup, text=event_data["name"], font=("Roboto", 12, "bold"), bg=popup_bg, fg=fg).pack(padx=10, pady=(10,2))
        tk.Label(popup, text=f"Date: {event_data['date']}", bg=popup_bg, fg=fg).pack(anchor="w", padx=10)
        tk.Label(popup, text=f"Time: {event_data['time']} - {event_data['end_time']}", bg=popup_bg, fg=fg).pack(anchor="w", padx=10)
        tk.Label(popup, text=f"Description: {event_data['description']}", bg=popup_bg, fg=fg, wraplength=250, justify="left").pack(anchor="w", padx=10, pady=(0,10))
        tk.Button(popup, text="Close", command=popup.destroy, bg="#444" if theme_mode == "dark" else "#e0e0e0", fg=fg).pack(pady=(0,10))

    def on_event_hover(event_id, event_data):
        def enter(e):
            def show():
                x = root.winfo_pointerx() + 10
                y = root.winfo_pointery() + 10
                show_event_popup(event_data, x, y)
            draw_events.hover_after = root.after(500, show)
        def leave(e):
            if hasattr(draw_events, "hover_after"):
                root.after_cancel(draw_events.hover_after)
            if hasattr(draw_events, "popup") and draw_events.popup:
                try:
                    draw_events.popup.destroy()
                except Exception:
                    pass
        schedule_canvas.tag_bind(event_id, "<Enter>", enter)
        schedule_canvas.tag_bind(event_id, "<Leave>", leave)

    def on_event_double_click(event_id, event_data):
        def double_click(e):
            open_update_event_window(event_data)
        schedule_canvas.tag_bind(event_id, "<Double-Button-1>", double_click)

    # --- Drawing logic ---
    if view_mode == "Daily":
        row_height = daily_weekly_row_height
        col_width = daily_weekly_col_width
        events_today = []
        for event in events:
            event_name, event_date, start_time, end_time, description, event_color, employee_id = event
            if isinstance(event_date, (datetime, date)):
                event_date = event_date.strftime("%Y-%m-%d")
            if event_date == start_date:
                events_today.append(event)
        # Group overlapping events
        def get_overlapping_groups(events):
            events = sorted(events, key=lambda e: e[2])
            groups = []
            current_group = []
            for event in events:
                if not current_group:
                    current_group.append(event)
                else:
                    last_end = current_group[-1][3]
                    if event[2] < last_end:
                        current_group.append(event)
                    else:
                        groups.append(current_group)
                        current_group = [event]
            if current_group:
                groups.append(current_group)
            return groups
        groups = get_overlapping_groups(events_today)
        for group in groups:
            n = len(group)
            for idx, event in enumerate(group):
                event_name, event_date, start_time, end_time, description, event_color, employee_id = event
                if isinstance(start_time, timedelta):
                    start_time_str = timedelta_to_str(start_time)
                else:
                    start_time_str = start_time.strftime("%H:%M:%S")

                if isinstance(end_time, timedelta):
                    end_time_str = timedelta_to_str(end_time)
                else:
                    end_time_str = end_time.strftime("%H:%M:%S")

                # Parse start and end hour/minute from time strings
                start_hour, start_minute, _ = map(int, start_time_str.split(":"))
                end_hour, end_minute, _ = map(int, end_time_str.split(":"))

                start_hour_decimal = start_hour + start_minute / 60
                end_hour_decimal = end_hour + end_minute / 60
                # ...use start_hour_decimal and end_hour_decimal below...
                y1 = (start_hour + 1) * row_height
                y2 = (end_hour_decimal + 1) * row_height
                y1 = (start_hour + 1) * row_height
                y2 = (end_hour + 1) * row_height
                x1 = col_width + (col_width / n) * idx
                x2 = x1 + (col_width / n)
                event_data_dict = {
                    "name": event_name,
                    "date": event_date,
                    "time": start_time_str,
                    "end_time": end_time_str,
                    "description": description,
                    "color": event_color,
                    "employee_id": employee_id,
                }
                rect_id = schedule_canvas.create_rectangle(x1, y1, x2, y2, fill=event_color, outline="white")
                text_id = schedule_canvas.create_text(
                    (x1 + x2) / 2, (y1 + y2) / 2,
                    text=event_name,
                    fill="white",
                    font=("Roboto", 10, "bold"),
                    width=(col_width / n) - 10
                )
                on_event_hover(rect_id, event_data_dict)
                on_event_hover(text_id, event_data_dict)
                on_event_double_click(rect_id, event_data_dict)
                on_event_double_click(text_id, event_data_dict)

    elif view_mode == "Weekly":
        row_height = daily_weekly_row_height
        col_width = daily_weekly_col_width
        events_by_day = {}
        for event in events:
            event_name, event_date, start_time, end_time, description, event_color, employee_id = event
            if isinstance(event_date, (datetime, date)):
                event_date = event_date.strftime("%Y-%m-%d")
            events_by_day.setdefault(event_date, []).append(event)
        def get_overlapping_groups(events):
            events = sorted(events, key=lambda e: e[2])
            groups = []
            current_group = []
            for event in events:
                if not current_group:
                    current_group.append(event)
                else:
                    last_end = current_group[-1][3]
                    if event[2] < last_end:
                        current_group.append(event)
                    else:
                        groups.append(current_group)
                        current_group = [event]
            if current_group:
                groups.append(current_group)
            return groups
        for i in range(7):
            day = (start_date_obj + timedelta(days=i)).strftime("%Y-%m-%d")
            day_events = events_by_day.get(day, [])
            groups = get_overlapping_groups(day_events)
            for group in groups:
                n = len(group)
                for idx, event in enumerate(group):
                    event_name, event_date, start_time, end_time, description, event_color, employee_id = event
                    if isinstance(start_time, timedelta):
                        start_hour = start_time.seconds // 3600
                        start_minute = (start_time.seconds % 3600) // 60
                        start_time_str = f"{start_hour:02d}:{start_minute:02d}:00"
                    else:
                        start_hour = start_time.hour
                        start_minute = start_time.minute
                        start_time_str = start_time.strftime("%H:%M:%S")

                    if isinstance(end_time, timedelta):
                        end_hour = end_time.seconds // 3600
                        end_minute = (end_time.seconds % 3600) // 60
                        end_time_str = f"{end_hour:02d}:{end_minute:02d}:00"
                    else:
                        end_hour = end_time.hour
                        end_minute = end_time.minute
                        end_time_str = end_time.strftime("%H:%M:%S")

                    start_hour_decimal = start_hour + start_minute / 60
                    end_hour_decimal = end_hour + end_minute / 60
                    y1 = (start_hour + 1) * row_height
                    y2 = (end_hour_decimal + 1) * row_height
                    x1 = col_width * (i + 1) + (col_width / n) * idx
                    x2 = x1 + (col_width / n)
                    event_data_dict = {
                        "name": event_name,
                        "date": event_date,
                        "time": start_time_str,
                        "end_time": end_time_str,
                        "description": description,
                        "color": event_color,
                        "employee_id": employee_id,
                    }  
                    rect_id = schedule_canvas.create_rectangle(x1, y1, x2, y2, fill=event_color, outline="white")
                    text_id = schedule_canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=event_name,
                        fill="white",
                        font=("Roboto", 10, "bold"),
                        width=(col_width / n) - 10
                    )
                    on_event_hover(rect_id, event_data_dict)
                    on_event_hover(text_id, event_data_dict)
                    on_event_double_click(rect_id, event_data_dict)
                    on_event_double_click(text_id, event_data_dict)

    elif view_mode == "Monthly":
        row_height = monthly_row_height
        col_width = monthly_col_width
        first_day = start_date_obj.replace(day=1)
        first_weekday = first_day.weekday()
        next_month = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1)
        days_in_month = (next_month - timedelta(days=1)).day
        total_cells = first_weekday + days_in_month
        num_rows = (total_cells + 6) // 7

        # Organize events by day
        events_by_day = {}
        for event in events:
            event_name, event_date, start_time, end_time, description, event_color, employee_id = event
            day = int(datetime.strptime(str(event_date), "%Y-%m-%d").day)
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

        max_events_per_cell = 5  # Show up to 5, then "+N more"
        day = 1
        for row in range(num_rows):
            for col in range(7):
                cell_idx = row * 7 + col
                x1 = col * col_width
                y1 = (row + 1) * row_height
                if cell_idx >= first_weekday and day <= days_in_month:
                    events_today = events_by_day.get(day, [])
                    for i, event in enumerate(events_today[:max_events_per_cell]):
                        y_event = y1 + 22 + i * 16
                        schedule_canvas.create_rectangle(x1 + 5, y_event, x1 + col_width - 5, y_event + 14, fill=event[5], outline="")
                        schedule_canvas.create_text(x1 + 12, y_event + 7, text=event[0], anchor="w", fill=cell_fg, font=("Roboto", 9), width=col_width-24)
                    # "+N more" link
                    if len(events_today) > max_events_per_cell:
                        def show_popup(event=None, day=day, events_today=events_today):
                            popup_win = tk.Toplevel(root)
                            popup_win.title(f"Events for {start_date_obj.strftime('%A')}, {start_date_obj.strftime('%B')} {day}")
                            popup_win.geometry("320x420")
                            popup_win.configure(bg=popup_bg)
                            tk.Label(
                                popup_win,
                                text=f"{start_date_obj.strftime('%A')}, {start_date_obj.strftime('%B')} {day}",
                                font=("Roboto", 12, "bold"),
                                bg=popup_bg,
                                fg=popup_fg
                            ).pack(pady=10)
                            for ev in events_today:
                                tk.Label(
                                    popup_win,
                                    text=ev[0],
                                    bg=ev[5],
                                    fg="white" if theme_mode == "dark" else "#000",
                                    anchor="w",
                                    font=("Roboto", 10),
                                    padx=8,
                                    pady=2
                                ).pack(fill="x", padx=12, pady=2)
                            tk.Button(
                                popup_win,
                                text="Close",
                                command=popup_win.destroy,
                                bg="#444" if theme_mode == "dark" else "#e0e0e0",
                                fg="#fff" if theme_mode == "dark" else "#000"
                            ).pack(pady=12)
                        y_more = y1 + 22 + max_events_per_cell * 16
                        more_text = f"+{len(events_today) - max_events_per_cell} more"
                        tag = f"more_{row}_{col}"
                        schedule_canvas.create_text(
                            x1 + 12, y_more,
                            text=more_text,
                            anchor="w",
                            fill="#1e88e5",
                            font=("Roboto", 9, "underline"),
                            tags=tag
                        )
                        schedule_canvas.tag_bind(tag, "<Button-1>", show_popup)
                    day += 1

def fetch_events():
    global current_start_date, current_end_date  # Use the global date range
    selected_date = calendar.get_date()
    view_mode = view_mode_var.get()

    # Calculate the date range based on the view mode
    if view_mode == "Daily":
        current_start_date = selected_date
        current_end_date = selected_date
    elif view_mode == "Weekly":
        current_start_date = selected_date
        current_end_date = (datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")
    elif view_mode == "Monthly":
        current_start_date = selected_date
        current_end_date = (datetime.strptime(selected_date, "%Y-%m-%d").replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%Y-%m-%d")
        current_end_date = (datetime.strptime(current_end_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching events for {view_mode} view: {current_start_date} to {current_end_date}")  # Debugging statement

    try:
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute('''
            SELECT EventName, EventDate, EventStartTime, EventEndTime, Description, EventColor, EmployeeID
            FROM Events
            WHERE EventDate BETWEEN ? AND ?
        ''', (current_start_date, current_end_date))
            events = cursor.fetchall()
            connection.close()

            events = [
                (
                    event[0],  # EventName
                    event[1],  # EventDate
                    event[2],  # EventStartTime
                    event[3],  # EventEndTime
                    event[4],  # Description
                    event[5],  # EventColor
                    event[6],  # EmployeeID
                )
                for event in events
            ]

            # Debugging: Print fetched events
            print(f"Fetched events: {events}")

            # Fetch the updated employee list
            employees = fetch_employee_names()
            print(f"Employees: {employees}")  # Debugging statement

            # Clear the schedule view and redraw the grid
            schedule_canvas.delete("all")  # Clear everything from the canvas
            draw_grid(current_start_date, current_end_date, employees, view_mode)
            draw_events(events, current_start_date, employees, view_mode)  # Pass view_mode to draw_events

            # Update the scroll region dynamically
            schedule_canvas.configure(scrollregion=schedule_canvas.bbox("all"))

            # Reapply layout to ensure proper resizing
            schedule_canvas.update_idletasks()
    except Exception as e:
        print("Error retrieving events:", e)  # Debugging statement
        traceback.print_exc()  # Print detailed error to the terminal
        messagebox.showerror("Database Error", f"Error retrieving events: {e}")

# Initialize the application
def setup_layout():
    create_sidebar()
    create_top_toolbar()
    create_notebook()
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)

def open_employee_profile_window(employee_data=None):
    """
    Opens a window to add or update an employee's profile.

    Args:
        employee_data (dict, optional): A dictionary containing employee details for updating. Defaults to None.
    """
    # Create a pop-up window for the employee profile
    profile_window = tk.Toplevel(root)
    profile_window.title("Employee Profile")
    profile_window.geometry("500x500")

    # Labels and Entry fields for employee details
    tk.Label(profile_window, text="Last Name:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    last_name_entry = tk.Entry(profile_window, width=30)
    last_name_entry.grid(row=0, column=1, padx=10, pady=5)
    if employee_data:
        last_name_entry.insert(0, employee_data.get("last_name", ""))

    tk.Label(profile_window, text="First Name:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
    first_name_entry = tk.Entry(profile_window, width=30)
    first_name_entry.grid(row=0, column=3, padx=10, pady=5)
    if employee_data:
        first_name_entry.insert(0, employee_data.get("first_name", ""))

    tk.Label(profile_window, text="Address:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    address_entry = tk.Entry(profile_window, width=60)
    address_entry.grid(row=1, column=1, columnspan=3, padx=10, pady=5)
    if employee_data:
        address_entry.insert(0, employee_data.get("address", ""))

    tk.Label(profile_window, text="City:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
    city_entry = tk.Entry(profile_window, width=20)
    city_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        city_entry.insert(0, employee_data.get("city", ""))

    tk.Label(profile_window, text="State:").grid(row=2, column=2, padx=10, pady=5, sticky="e")
    state_entry = tk.Entry(profile_window, width=10)
    state_entry.grid(row=2, column=3, padx=10, pady=5, sticky="w")
    if employee_data:
        state_entry.insert(0, employee_data.get("state", ""))

    tk.Label(profile_window, text="Zip:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
    zip_entry = tk.Entry(profile_window, width=10)
    zip_entry.grid(row=3, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        zip_entry.insert(0, employee_data.get("zip", ""))

    tk.Label(profile_window, text="Phone:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
    phone_entry = tk.Entry(profile_window, width=20)
    phone_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        phone_entry.insert(0, employee_data.get("phone", ""))

    tk.Label(profile_window, text="Email:").grid(row=4, column=2, padx=10, pady=5, sticky="e")
    email_entry = tk.Entry(profile_window, width=30)
    email_entry.grid(row=4, column=3, padx=10, pady=5)
    if employee_data:
        email_entry.insert(0, employee_data.get("email", ""))

    tk.Label(profile_window, text="DL Number:").grid(row=5, column=0, padx=10, pady=5, sticky="e")
    dl_entry = tk.Entry(profile_window, width=20)
    dl_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
    if employee_data:
        dl_entry.insert(0, employee_data.get("dl_number", ""))

    # Buttons for saving or canceling
    def save_employee():
        # Collect data from the fields
        employee_details = {
            "last_name": last_name_entry.get(),
            "first_name": first_name_entry.get(),
            "address": address_entry.get(),
            "city": city_entry.get(),
            "state": state_entry.get(),
            "zip": zip_entry.get(),
            "phone": phone_entry.get(),
            "email": email_entry.get(),
            "dl_number": dl_entry.get(),
        }
        print("Employee Details Saved:", employee_details)  # Debugging statement
        profile_window.destroy()

    tk.Button(profile_window, text="Save", command=save_employee).grid(row=6, column=1, pady=20)
    tk.Button(profile_window, text="Cancel", command=profile_window.destroy).grid(row=6, column=2, pady=20)


if __name__ == "__main__":
    show_connection_screen()
    root.mainloop()
