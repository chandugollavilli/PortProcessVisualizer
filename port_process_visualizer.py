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