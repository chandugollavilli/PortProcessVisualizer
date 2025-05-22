Port and Process Activity Visualizer 🚀

A powerful Python-based application for monitoring network port and process activity in real-time on Windows systems. This tool provides a sleek web interface to visualize active ports, filter by port or process, display GeoIP locations for remote IPs, export logs as CSV/JSON, and generate alerts for suspicious port usage. Perfect for network administrators, security analysts, or developers looking to track system activity with ease.
📋 Table of Contents

Features
Screenshots
Installation
Usage
Testing
Troubleshooting
Contributing
License
Contact

✨ Features

Real-Time Monitoring: Tracks active ports and processes every 10 seconds using psutil.
Web-Based UI: Intuitive interface with a table and timeline chart for port usage.
Filters: Search by specific ports (e.g., 8000) or process names (e.g., python.exe).
GeoIP Lookup: Displays city and country for remote IPs via ip-api.com.
Log Exports: Download port activity logs as CSV or JSON for analysis.
Alerts: Logs suspicious activity (e.g., non-standard processes on ports < 1024) to alerts.log.
Thread-Safe Database: Uses SQLite with a robust DatabaseManager for reliable data storage.
Windows Optimized: Tailored for Windows 10/11 with exclusions for system processes like svchost.exe.

📸 Screenshots
Coming soon! Example screenshots of the web UI, table, and timeline chart will be added.
🛠 Installation
Follow these steps to set up the project on a Windows system. For detailed instructions, refer to SOP_Port_Process_Visualizer.md.
Prerequisites

Windows 10 or 11
Python 3.8 or higher
Git (optional, for cloning)
Internet access (for GeoIP lookups)
Administrator privileges (for full psutil functionality)

Steps

Create Working Directory:
mkdir C:\Temp\ports
cd C:\Temp\ports
icacls C:\Temp\ports /grant Everyone:F


Clone the Repository (or copy files manually):
git clone https://github.com/your-username/port-process-visualizer.git
cd port-process-visualizer

Replace your-username with your GitHub username.

Install Dependencies:
pip install psutil flask requests


Verify Files:Ensure port_process_visualizer.py, SOP_Port_Process_Visualizer.md, and templates/index.html are present:
dir



🚀 Usage

Run the Application:

Open an elevated PowerShell (Run as administrator):cd C:\Temp\ports
python port_process_visualizer.py


Expected output: Running on http://127.0.0.1:5000.


Access the Web UI:

Open a browser and navigate to http://localhost:5000.
Explore the table, apply filters, view the timeline chart, and export logs.


Generate Test Data:

Start a test server:python -m http.server 8000


Check the UI for python.exe on port 8000.
Stop the server:taskkill /IM python.exe /F




Monitor Alerts:

Run a server on a low port (requires admin):python -m http.server 80


Check alerts.log:type alerts.log





For detailed usage, see SOP_Port_Process_Visualizer.md.
🧪 Testing
Test the core features to ensure the application works as expected. Refer to Section 5.3 of SOP_Port_Process_Visualizer.md for comprehensive testing steps.

Database:
import sqlite3
conn = sqlite3.connect('port_activity.db')
c = conn.cursor()
c.execute("PRAGMA table_info(port_activity)")
print(c.fetchall())
conn.close()


Expected: Includes timestamp, pid, process_name, port, protocol, remote_ip, status, location.


UI Filters:

Filter by port “8000” or process “python” in the UI.
Expected: Table updates to show only matching entries.


GeoIP Lookup:
curl http://example.com


Check the UI’s “Location” column for city/country (e.g., “Mumbai, India”).


Exports:

Click “Export as CSV” or “Export as JSON” in the UI.
Verify downloaded files.


Alerts:

Check alerts.log after running a server on port 80.



🛡️ Troubleshooting

Database Errors (e.g., “database is locked”):
Delete port_activity.db and restart:del port_activity.db
python port_process_visualizer.py




UI Not Updating:
Check browser console (F12) for JavaScript errors.
Test /api/data:curl http://localhost:5000/api/data




GeoIP Issues:
Verify ip-api.com access:curl http://ip-api.com/json/8.8.8.8


Check app.log for errors:type app.log




General:
Run PowerShell as administrator.
Ensure working in C:\Temp\ports.



See Section 5.4 of SOP_Port_Process_Visualizer.md for detailed troubleshooting.
🤝 Contributing
Contributions are welcome! To contribute:

Fork the repository.
Create a branch:git checkout -b feature/your-feature


Commit changes:git commit -m "Add your feature"


Push and create a pull request:git push origin feature/your-feature



Please follow the coding style in port_process_visualizer.py and update SOP_Port_Process_Visualizer.md if necessary.
📜 License
This project is licensed under the MIT License. See the LICENSE file for details.
📬 Contact
For issues or suggestions, open an issue on GitHub or contact the maintainer at your.email@example.com (replace with your email). Provide app.log and steps to reproduce any issues.

Built with ❤️ using Python, Flask, and SQLite. Happy monitoring!
