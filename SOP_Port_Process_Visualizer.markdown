# Standard Operating Procedure (SOP) for Port and Process Activity Visualizer

## 1. Purpose
This Standard Operating Procedure (SOP) outlines the steps to install, configure, run, test, troubleshoot, and maintain the Port and Process Activity Visualizer, a Python-based application for monitoring network port and process activity on a Windows system. The application provides a web-based UI with real-time data, filters for ports/processes, GeoIP lookup for remote IPs, CSV/JSON log exports, and alerts for suspicious port activity. The complete application code is included in Appendix A for reference.

## 2. Scope
This SOP applies to users, system administrators, or developers deploying the application on a Windows system (e.g., Windows 10/11). It covers setup, operation, testing, and basic maintenance for development or testing environments. Production deployment considerations are noted but not fully detailed.

## 3. Responsibilities
- **User/Administrator**: Installs dependencies, runs the application, tests functionality, and monitors logs.
- **Developer (if applicable)**: Handles code modifications, enhancements, or bug fixes based on user feedback or issues.
- **Network/System Admin**: Ensures network access for GeoIP lookups and admin privileges for full functionality.

## 4. Prerequisites
- **Operating System**: Windows 10 or 11.
- **Hardware**: Minimum 4GB RAM, 1GB free disk space.
- **Software**:
  - Python 3.8 or higher (download from `python.org`).
  - pip (Python package manager, included with Python).
  - Web browser (e.g., Chrome, Edge, Firefox).
- **Permissions**: Administrator privileges to capture all network connections via `psutil`.
- **Internet Access**: Required for GeoIP lookups via `ip-api.com`.
- **Working Directory**: `C:\Temp\ports` (recommended to avoid OneDrive syncing issues).

## 5. Procedure

### 5.1 Installation
1. **Create Working Directory**:
   - Open an elevated PowerShell (right-click, “Run as administrator”).
   - Create and navigate to the directory:
     ```powershell
     mkdir C:\Temp\ports
     cd C:\Temp\ports
     ```
   - Grant write permissions:
     ```powershell
     icacls C:\Temp\ports /grant Everyone:F
     ```

2. **Install Python Dependencies**:
   - Install required packages (`psutil`, `flask`, `requests`):
     ```powershell
     pip install psutil flask requests
     ```
   - Verify installation:
     ```powershell
     pip list
     ```
     - Expected: Lists `psutil`, `flask`, `requests` with versions.

3. **Save Application Code**:
   - Copy the code from Appendix A (or the separate `port_process_visualizer.py` artifact) to `C:\Temp\ports\port_process_visualizer.py`.
   - Ensure the script includes:
     - Thread-safe `DatabaseManager` for SQLite operations.
     - UI filters for ports/processes.
     - GeoIP lookup using `ip-api.com`.
     - CSV/JSON export routes.
     - Schema migration for the `location` column.

### 5.2 Running the Application
1. **Start the Application**:
   - In the elevated PowerShell, navigate to `C:\Temp\ports`:
     ```powershell
     cd C:\Temp\ports
     ```
   - Run the script:
     ```powershell
     python port_process_visualizer.py
     ```
   - Verify output:
     - Expected: `Running on http://127.0.0.1:5000`.
     - Note: Ignore the warning “This is a development server” for testing.

2. **Access the Web UI**:
   - Open a web browser (e.g., Chrome, Edge).
   - Navigate to `http://localhost:5000`.
   - Expected: Displays a table with port/process data, filter inputs, export links, and a timeline chart.

### 5.3 Testing Core Features
1. **Database Initialization**:
   - Check for `port_activity.db` in `C:\Temp\ports`:
     ```powershell
     dir port_activity.db
     ```
   - Verify schema:
     ```python
     import sqlite3
     conn = sqlite3.connect('port_activity.db')
     c = conn.cursor()
     c.execute("PRAGMA table_info(port_activity)")
     print(c.fetchall())
     conn.close()
     ```
     - Expected: Columns include `timestamp`, `pid`, `process_name`, `port`, `protocol`, `remote_ip`, `status`, `location`.
   - Check `app.log`:
     ```powershell
     type app.log
     ```
     - Expected: “Database initialized successfully” and optionally “Added location column to port_activity table”.

2. **Data Collection**:
   - Start a test server to generate network activity:
     ```powershell
     python -m http.server 8000
     ```
   - Wait 20 seconds, then query the database:
     ```python
     import sqlite3
     conn = sqlite3.connect('port_activity.db')
     c = conn.cursor()
     c.execute("SELECT * FROM port_activity WHERE port = 8000")
     print(c.fetchall())
     conn.close()
     ```
     - Expected: Entries for `python.exe` on port 8000 with `tcp` protocol.
   - Stop the server:
     ```powershell
     taskkill /IM python.exe /F
     ```

3. **UI Filters**:
   - In the UI (`http://localhost:5000`), enter “8000” in the port filter and click “Apply Filters”.
     - Expected: Table shows only port 8000 entries.
   - Enter “python” in the process filter and click “Apply Filters”.
     - Expected: Table shows only `python.exe` entries.
   - Clear filters to view all data.

4. **GeoIP Lookup**:
   - Generate a remote connection:
     ```powershell
     curl http://example.com
     ```
   - Check the UI’s “Location” column.
     - Expected: Shows city and country (e.g., “Mumbai, India”) or “Unknown” for local/failed lookups.
   - Verify `app.log` for GeoIP errors:
     ```powershell
     type app.log
     ```

5. **Log Export**:
   - In the UI, click “Export as CSV” or “Export as JSON”.
     - CSV: Downloads `port_activity.csv` with columns: Timestamp, PID, Process Name, Port, Protocol, Remote IP, Status, Location.
     - JSON: Displays JSON with the same fields.
   - Verify CSV:
     ```powershell
     type port_activity.csv
     ```

6. **Alerts**:
   - Run a server on a low port (requires admin):
     ```powershell
     python -m http.server 80
     ```
   - Check `alerts.log`:
     ```powershell
     type alerts.log
     ```
     - Expected: Alert like `[ALERT] <timestamp>: Suspicious port 80 used by python.exe`.
   - Stop the server:
     ```powershell
     taskkill /IM python.exe /F
     ```

7. **Timeline Chart**:
   - In the UI, verify the “Port Usage Timeline” chart updates every 10 seconds with port counts.
   - Start/stop servers (e.g., `python -m http.server 8001`) and confirm chart reflects changes.

### 5.4 Troubleshooting
1. **Database Errors**:
   - **Symptom**: Errors like “database is locked” or “no such column” in `app.log`.
   - **Action**:
     - Ensure no other processes (e.g., SQLite clients) access `port_activity.db`.
     - Delete `port_activity.db` and restart the script to recreate the table:
       ```powershell
       del port_activity.db
       python port_process_visualizer.py
       ```
     - Increase `DatabaseManager` retries (edit `retries = 5` in `port_process_visualizer.py`).

2. **UI Issues**:
   - **Symptom**: Table/chart not updating or filters not working.
   - **Action**:
     - Open browser console (F12) and check for JavaScript errors.
     - Verify `/api/data` endpoint (e.g., `curl http://localhost:5000/api/data`).
     - Clear browser cache or try a different browser.

3. **GeoIP Failures**:
   - **Symptom**: “Location” column shows “Unknown” for remote IPs.
   - **Action**:
     - Check `app.log` for `requests` errors.
     - Test `ip-api.com`:
       ```powershell
       curl http://ip-api.com/json/8.8.8.8
       ```
     - Ensure internet connectivity and no firewall blocking `ip-api.com`.

4. **Export Failures**:
   - **Symptom**: CSV/JSON downloads fail or are empty.
   - **Action**:
     - Check `app.log` for database errors.
     - Verify disk space in `C:\Temp\ports`.
     - Test endpoint directly:
       ```powershell
       curl http://localhost:5000/api/export/csv
       ```

5. **General Issues**:
   - Ensure PowerShell is run as administrator.
   - Confirm working in `C:\Temp\ports` (not OneDrive).
   - Check `app.log` for detailed errors:
     ```powershell
     type app.log
     ```

### 5.5 Maintenance
1. **Monitor Logs**:
   - Regularly check `app.log` and `alerts.log` for errors or suspicious activity:
     ```powershell
     type app.log
     type alerts.log
     ```
   - Archive logs periodically to prevent large file sizes:
     ```powershell
     move app.log app.log.bak
     move alerts.log alerts.log.bak
     ```

2. **Update Dependencies**:
   - Update Python packages monthly:
     ```powershell
     pip install --upgrade psutil flask requests
     ```

3. **Backup Database**:
   - Back up `port_activity.db` before major changes:
     ```powershell
     copy port_activity.db port_activity.db.bak
     ```

4. **Code Updates**:
   - Check for script updates from the developer (if applicable).
   - Test updates in a separate directory (e.g., `C:\Temp\ports_test`) before deploying.

### 5.6 Production Considerations
- **Server**: Replace Flask’s development server with a WSGI server (e.g., Gunicorn):
  ```powershell
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 port_process_visualizer:app
  ```
- **Database**: Consider PostgreSQL for better concurrency:
  - Install PostgreSQL and `psycopg2` (`pip install psycopg2`).
  - Modify script to use PostgreSQL (contact developer for assistance).
- **Security**:
  - Add authentication to UI and API endpoints.
  - Use HTTPS for production (e.g., via Nginx reverse proxy).
- **GeoIP Limits**: Monitor `ip-api.com` rate limits (45 requests/minute for free tier). Consider a paid API or caching for high traffic.

## 6. References
- **Application Code**: `C:\Temp\ports\port_process_visualizer.py` (see Appendix A).
- **Logs**: `C:\Temp\ports\app.log`, `C:\Temp\ports\alerts.log`.
- **GeoIP API**: `http://ip-api.com` (free tier, 45 requests/minute).
- **Dependencies**: `psutil`, `flask`, `requests` (install via `pip`).

## 7. Revision History
- **Version 1.0**: Created on May 22, 2025, for initial deployment on Windows.
- **Version 1.1**: Updated on May 22, 2025, to include complete application code in Appendix A.
- **Author**: Grok 3, xAI (based on user interactions and code updates).

## 8. Contact
- For issues or enhancements, contact the developer or system administrator.
- Report errors with `app.log` contents and steps to reproduce.

## Appendix A: Application Code
Below is the complete code for `port_process_visualizer.py`, which implements the Port and Process Activity Visualizer with all features (real-time monitoring, UI filters, GeoIP lookup, CSV/JSON export, alerts, and schema migration).

```python
import psutil
import sqlite3
import time
from datetime import datetime
import threading
from flask import Flask, render_template, send_file, request
import json
import logging
import os
import queue
import requests
import csv
import io

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)

# Thread-safe database connection manager
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()

    def execute(self, query, params=(), fetch=False):
        retries = 3
        for attempt in range(retries):
            try:
                with self.lock:
                    conn = sqlite3.connect(self.db_path, timeout=10)
                    c = conn.cursor()
                    c.execute(query, params)
                    result = c.fetchall() if fetch else None
                    conn.commit()
                    conn.close()
                    return result
            except sqlite3.OperationalError as e:
                logging.error(f"Database error (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(1)
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                raise
            finally:
                if 'conn' in locals():
                    conn.close()

# Initialize SQLite database
def init_db(db_manager):
    try:
        # Create table if it doesn't exist
        db_manager.execute('''CREATE TABLE IF NOT EXISTS port_activity
                         (timestamp TEXT, pid INTEGER, process_name TEXT, port INTEGER,
                          protocol TEXT, remote_ip TEXT, status TEXT)''')
        
        # Check if location column exists and add it if missing
        result = db_manager.execute('''PRAGMA table_info(port_activity)''', fetch=True)
        columns = [row[1] for row in result]
        if 'location' not in columns:
            db_manager.execute('''ALTER TABLE port_activity ADD COLUMN location TEXT''')
            logging.info("Added location column to port_activity table")
        
        logging.info("Database initialized successfully")
    except sqlite3.OperationalError as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

# GeoIP lookup using ip-api.com
def get_geoip(ip):
    if not ip or ip in ('', '0.0.0.0', '::'):
        return ''
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return f"{data.get('city', '')}, {data.get('country', '')}"
        return 'Unknown'
    except requests.RequestException as e:
        logging.error(f"GeoIP lookup failed for {ip}: {e}")
        return 'Unknown'

# Collect port and process data
def collect_data(db_manager):
    try:
        timestamp = datetime.now().isoformat()
        connections = psutil.net_connections(kind='inet')
        
        for conn in connections:
            if conn.laddr:
                pid = conn.pid if conn.pid else 0
                try:
                    process_name = psutil.Process(pid).name() if pid else "unknown"
                except psutil.NoSuchProcess:
                    process_name = "unknown"
                remote_ip = conn.raddr.ip if conn.raddr else ''
                location = get_geoip(remote_ip)
                db_manager.execute('''INSERT INTO port_activity
                                    (timestamp, pid, process_name, port, protocol, remote_ip, status, location)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (timestamp, pid, process_name, conn.laddr.port,
                                  'tcp' if conn.type == 1 else 'udp',
                                  remote_ip, conn.status, location))
        
        suspicious_ports = db_manager.execute('''
            SELECT timestamp, port, process_name FROM port_activity
            WHERE port < 1024 AND process_name NOT IN ('sshd', 'nginx', 'apache2', 'System', 'svchost.exe')
            AND timestamp = ?
        ''', (timestamp,), fetch=True)
        
        if suspicious_ports:
            with open('alerts.log', 'a') as f:
                for row in suspicious_ports:
                    f.write(f"[ALERT] {row[0]}: Suspicious port {row[1]} used by {row[2]}\n")
        
        logging.info("Data collected successfully")
    except sqlite3.OperationalError as e:
        logging.error(f"Database error in collect_data: {e}")
    except Exception as e:
        logging.error(f"Error in collect_data: {e}")

# Background data collection thread
def data_collection_thread(db_manager):
    while True:
        collect_data(db_manager)
        time.sleep(10)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    try:
        db_manager = DatabaseManager('port_activity.db')
        port_filter = request.args.get('port', '')
        process_filter = request.args.get('process', '')
        
        query = '''
            SELECT DISTINCT pid, process_name, port, protocol, remote_ip, status, location
            FROM port_activity
            WHERE timestamp = (SELECT MAX(timestamp) FROM port_activity)
        '''
        params = []
        if port_filter:
            query += ' AND port = ?'
            params.append(int(port_filter))
        if process_filter:
            query += ' AND process_name LIKE ?'
            params.append(f'%{process_filter}%')
        
        snapshot = db_manager.execute(query, params, fetch=True)
        
        timeline = db_manager.execute('''
            SELECT timestamp, COUNT(DISTINCT port) as port_count
            FROM port_activity
            GROUP BY timestamp
            ORDER BY timestamp DESC
            LIMIT 50
        ''', fetch=True)
        
        return json.dumps({
            'snapshot': [{
                'pid': row[0],
                'process_name': row[1],
                'port': row[2],
                'protocol': row[3],
                'remote_ip': row[4],
                'status': row[5],
                'location': row[6]
            } for row in snapshot],
            'timeline': [{
                'timestamp': row[0],
                'port_count': row[1]
            } for row in timeline]
        })
    except sqlite3.OperationalError as e:
        logging.error(f"Database error in get_data: {e}")
        return json.dumps({'snapshot': [], 'timeline': []})
    except Exception as e:
        logging.error(f"Error in get_data: {e}")
        return json.dumps({'snapshot': [], 'timeline': []})

@app.route('/api/export/<format>')
def export_logs(format):
    try:
        db_manager = DatabaseManager('port_activity.db')
        data = db_manager.execute('''
            SELECT timestamp, pid, process_name, port, protocol, remote_ip, status, location
            FROM port_activity
            ORDER BY timestamp DESC
        ''', fetch=True)
        
        if format.lower() == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Timestamp', 'PID', 'Process Name', 'Port', 'Protocol', 'Remote IP', 'Status', 'Location'])
            for row in data:
                writer.writerow(row)
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='port_activity.csv'
            )
        elif format.lower() == 'json':
            result = [{
                'timestamp': row[0],
                'pid': row[1],
                'process_name': row[2],
                'port': row[3],
                'protocol': row[4],
                'remote_ip': row[5],
                'status': row[6],
                'location': row[7]
            } for row in data]
            return json.dumps(result)
        else:
            return json.dumps({'error': 'Invalid format. Use csv or json'}), 400
    except sqlite3.OperationalError as e:
        logging.error(f"Database error in export_logs: {e}")
        return json.dumps({'error': 'Database error'}), 500
    except Exception as e:
        logging.error(f"Error in export_logs: {e}")
        return json.dumps({'error': 'Server error'}), 500

# HTML template
with open('templates/index.html', 'w') as f:
    f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Port Process Visualizer</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        canvas { max-width: 600px; margin: 20px; }
        .filter-container { margin-bottom: 20px; }
        .filter-container input { margin-right: 10px; padding: 5px; }
        .export-links { margin-top: 10px; }
    </style>
</head>
<body>
    <h2>Port and Process Activity</h2>
    <div class="filter-container">
        <input type="number" id="portFilter" placeholder="Filter by Port (e.g., 8000)">
        <input type="text" id="processFilter" placeholder="Filter by Process (e.g., python)">
        <button onclick="fetchData()">Apply Filters</button>
        <div class="export-links">
            <a href="/api/export/csv">Export as CSV</a> | <a href="/api/export/json">Export as JSON</a>
        </div>
    </div>
    <table>
        <tr>
            <th>PID</th>
            <th>Process</th>
            <th>Port</th>
            <th>Protocol</th>
            <th>Remote IP</th>
            <th>Status</th>
            <th>Location</th>
        </tr>
        <tbody id="tableBody"></tbody>
    </table>
    <h3>Port Usage Timeline</h3>
    <canvas id="timelineChart"></canvas>

    <script>
        async function fetchData() {
            try {
                const portFilter = document.getElementById('portFilter').value;
                const processFilter = document.getElementById('processFilter').value;
                const url = `/api/data${portFilter || processFilter ? '?' : ''}${portFilter ? `port=${portFilter}` : ''}${portFilter && processFilter ? '&' : ''}${processFilter ? `process=${processFilter}` : ''}`;
                const response = await fetch(url);
                const data = await response.json();
                
                // Update table
                const tableBody = document.getElementById('tableBody');
                tableBody.innerHTML = '';
                data.snapshot.forEach(row => {
                    tableBody.innerHTML += `
                        <tr>
                            <td>${row.pid}</td>
                            <td>${row.process_name}</td>
                            <td>${row.port}</td>
                            <td>${row.protocol}</td>
                            <td>${row.remote_ip}</td>
                            <td>${row.status}</td>
                            <td>${row.location}</td>
                        </tr>`;
                });
                
                // Update chart
                const ctx = document.getElementById('timelineChart').getContext('2d');
                if (window.myChart) window.myChart.destroy();
                window.myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.timeline.map(t => new Date(t.timestamp).toLocaleTimeString()),
                        datasets: [{
                            label: 'Active Ports',
                            data: data.timeline.map(t => t.port_count),
                            borderColor: 'blue',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        
        fetchData();
        setInterval(fetchData, 10000);
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    try:
        os.makedirs('templates', exist_ok=True)
        db_manager = DatabaseManager('port_activity.db')
        init_db(db_manager)
        threading.Thread(target=data_collection_thread, args=(db_manager,), daemon=True).start()
        app.run(debug=True)
    except Exception as e:
        logging.error(f"Startup error: {e}")
        print(f"Failed to start: {e}")
```