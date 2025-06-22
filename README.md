# Complex Scheduling App

A cross-platform, theme-aware scheduling and client management application with employee, client, and event management, recurring events, and Gmail integration (OAuth2).  
**No personal or tracing information is included in this repository.**

---

## Features

- **Employee, Client, and Event Management**  
  Add, update, and remove employees, clients, and events.
- **Recurring Events**  
  Supports daily, weekly, biweekly, monthly, and yearly recurring events.
- **Theme Support**  
  Switch between dark and light themes.
- **Gmail Integration**  
  Send emails to clients using Gmail OAuth2 (no passwords stored).
- **Photo and Attachment Support**  
  Store and view client photos and event attachments.
- **Database Connection Screen**  
  Users enter their own database credentials at startup (no credentials stored in code).
- **No Analytics or Tracking**  
  This app does not collect or transmit any personal data.

---

## Requirements

- Python 3.8+
- MariaDB or MySQL database  
  *(Use `schedule_schema.sql` to create the database: `mysql -u youruser -p < schedule_schema.sql`)*
- Gmail account (for email features)
- Python dependencies (see `requirements.txt`):
    - All other required modules are standard in Python (e.g., `tkinter`, `os`, `datetime`, etc.)

---

## Setup

1. **Clone the repository**
    ```sh
    git clone https://github.com/Darkkitten39/complex-scheduling-app
    cd complex-scheduling-app
    ```

2. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

3. **Prepare your database**
    - Create a MariaDB/MySQL database and tables as required by the app.
    - You will be prompted for DB credentials on app startup.

4. **Gmail Integration**
    - Go to [Google Cloud Console](https://console.cloud.google.com/).
    - Create a project and enable the Gmail API.
    - Download your `credentials.json` and place it in your user folder as described below.
    - The app will store OAuth tokens in a hidden folder in your home directory (`.my_schedule_app`).

5. **Run the app**
    ```sh
    python Complex_Scheduling_App.py
    ```

---

## Security & Privacy

- **No personal information, credentials, or tracking is present in this codebase.**
- **Database credentials are entered at runtime and never stored.**
- **Gmail OAuth2 is used; no passwords are stored.**
- **OAuth tokens and credentials are stored in your user home directory under `.my_schedule_app`.**
- **No analytics or telemetry is present.**

---

## File Locations

- **credentials.json**: Place your Gmail OAuth credentials here:
    - Windows: `C:\Users\<YourUser>\.my_schedule_app\credentials.json`
    - Linux/macOS: `/home/<youruser>/.my_schedule_app/credentials.json`
- **token.json**: Generated automatically after first Gmail login.

---

## Troubleshooting

- If you change Gmail scopes or credentials, delete `token.json` in `.my_schedule_app`.
- If you have database connection issues, check your DB credentials and network access.
- For Gmail issues, ensure your Google Cloud project has Gmail API enabled.

---

## License

MIT License

Copyright (c) 2025 Complex_Scheduling_App

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights  
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell     
copies of the Software, and to permit persons to whom the Software is         
furnished to do so, subject to the following conditions:                      

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.                               

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR    
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,      
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE   
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER       
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.

---

## Contact

For questions or issues, open an issue on GitHub or contact the maintainer.
