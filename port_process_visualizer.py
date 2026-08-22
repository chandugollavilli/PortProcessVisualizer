import psutil
import sqlite3
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template, send_file, request, jsonify, Response
import json
import logging
import os
import requests
import csv
import io
from logging.handlers import RotatingFileHandler

# Configure production rotating file logger for app.log
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s')

if not logger.handlers:
    app_handler = RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    app_handler.setFormatter(formatter)
    logger.addHandler(app_handler)

# Configure rotating file logger for security alerts
alert_logger = logging.getLogger('SecurityAlerts')
alert_logger.setLevel(logging.INFO)
if not alert_logger.handlers:
    alert_handler = RotatingFileHandler('alerts.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    alert_handler.setFormatter(logging.Formatter('%(message)s'))
    alert_logger.addHandler(alert_handler)

app = Flask(__name__)

# Global Database Path configuration
DB_PATH = 'port_activity.db'

# Enterprise Thread-Safe Database Manager with WAL Mode
class DatabaseManager:
    _lock = threading.Lock()

    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DB_PATH
        self._configure_wal()

    def _configure_wal(self):
        """Configure SQLite WAL mode for high concurrency concurrent reads/writes."""
        try:
            with DatabaseManager._lock:
                conn = sqlite3.connect(self.db_path, timeout=30)
                c = conn.cursor()
                c.execute('PRAGMA journal_mode=WAL;')
                c.execute('PRAGMA synchronous=NORMAL;')
                c.execute('PRAGMA busy_timeout=10000;')
                conn.commit()
                conn.close()
        except Exception as e:
            logging.error(f"Failed to configure SQLite WAL mode: {e}")

    def execute(self, query, params=(), fetch=False):
        retries = 5
        for attempt in range(retries):
            conn = None
            try:
                with DatabaseManager._lock:
                    conn = sqlite3.connect(self.db_path, timeout=30)
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    c.execute(query, params)
                    result = [dict(row) for row in c.fetchall()] if fetch else None
                    conn.commit()
                    return result
            except sqlite3.OperationalError as e:
                logging.warning(f"Database operational error (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(0.3)
            except Exception as e:
                logging.error(f"Unexpected database error: {e}")
                raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def execute_many(self, query, params_list):
        if not params_list:
            return
        retries = 5
        for attempt in range(retries):
            conn = None
            try:
                with DatabaseManager._lock:
                    conn = sqlite3.connect(self.db_path, timeout=30)
                    c = conn.cursor()
                    c.executemany(query, params_list)
                    conn.commit()
                    return
            except sqlite3.OperationalError as e:
                logging.warning(f"Database execute_many error (attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(0.3)
            except Exception as e:
                logging.error(f"Unexpected error in execute_many: {e}")
                raise
            finally:
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass

# Shared DB Manager instance accessor
def get_db_manager():
    return DatabaseManager(DB_PATH)

# Initialize Enterprise Database Tables, Migrations & Indices
def init_db(db_manager):
    try:
        # Table 1: Port Activity Snapshots
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS port_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                pid INTEGER,
                process_name TEXT,
                exe_path TEXT,
                port INTEGER,
                protocol TEXT,
                remote_ip TEXT,
                remote_port INTEGER,
                status TEXT,
                location TEXT
            )
        ''')

        # Schema Migrations check for legacy DBs
        result = db_manager.execute('''PRAGMA table_info(port_activity)''', fetch=True) or []
        columns = [row['name'] for row in result]
        if 'exe_path' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN exe_path TEXT')
            logging.info("Migrated port_activity: added exe_path column.")
        if 'remote_port' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN remote_port INTEGER')
            logging.info("Migrated port_activity: added remote_port column.")
        if 'location' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN location TEXT')
            logging.info("Migrated port_activity: added location column.")

        # Table 2: Security Threat Alerts
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                severity TEXT,
                pid INTEGER,
                process_name TEXT,
                port INTEGER,
                remote_ip TEXT,
                rule_name TEXT,
                description TEXT,
                status TEXT DEFAULT 'ACTIVE'
            )
        ''')

        # Table 3: Process Inventory & Telemetry
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS process_inventory (
                timestamp TEXT,
                pid INTEGER,
                process_name TEXT,
                exe_path TEXT,
                username TEXT,
                cpu_percent REAL,
                memory_mb REAL,
                open_ports INTEGER,
                PRIMARY KEY (timestamp, pid)
            )
        ''')

        # Indices for optimal query performance
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_timestamp ON port_activity(timestamp);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_port ON port_activity(port);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_proc ON port_activity(process_name);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON security_alerts(status);')

        logging.info("Database schema and indices initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing enterprise database: {e}")
        raise

# Network Subnet Helper
def is_private_ip(ip):
    if not ip or ip in ('', '0.0.0.0', '127.0.0.1', '::', '::1'):
        return True
    if ip.startswith(('10.', '192.168.', '127.', '169.254.', 'fe80:')):
        return True
    if ip.startswith('172.'):
        try:
            second_octet = int(ip.split('.')[1])
            if 16 <= second_octet <= 31:
                return True
        except (IndexError, ValueError):
            pass
    return False

# Persistent Process Object Cache for Accurate CPU % Calculations
PERSISTENT_PROC_CACHE = {}

def get_process_info(pid):
    if pid <= 0:
        return {
            'name': 'System Idle / Kernel',
            'exe': 'N/A',
            'username': 'NT AUTHORITY\\SYSTEM',
            'cpu': 0.0,
            'mem': 0.0,
            'ports': set()
        }

    proc = PERSISTENT_PROC_CACHE.get(pid)
    if proc:
        try:
            name = proc.name()
            exe = proc.exe() if hasattr(proc, 'exe') else 'N/A'
            username = proc.username() if hasattr(proc, 'username') else 'N/A'
            cpu = proc.cpu_percent(interval=None)
            mem = proc.memory_info().rss / (1024 * 1024) if hasattr(proc, 'memory_info') else 0.0
            return {
                'name': name,
                'exe': exe,
                'username': username,
                'cpu': cpu,
                'mem': mem,
                'ports': set()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            PERSISTENT_PROC_CACHE.pop(pid, None)

    try:
        p = psutil.Process(pid)
        name = p.name()
        exe = p.exe() if hasattr(p, 'exe') else 'N/A'
        username = p.username() if hasattr(p, 'username') else 'N/A'
        # Call cpu_percent once to initialize baseline interval
        p.cpu_percent(interval=None)
        mem = p.memory_info().rss / (1024 * 1024) if hasattr(p, 'memory_info') else 0.0
        PERSISTENT_PROC_CACHE[pid] = p
        return {
            'name': name,
            'exe': exe,
            'username': username,
            'cpu': 0.0,
            'mem': mem,
            'ports': set()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
        return {
            'name': 'System / Protected',
            'exe': 'N/A',
            'username': 'SYSTEM',
            'cpu': 0.0,
            'mem': 0.0,
            'ports': set()
        }

# Enterprise Asynchronous GeoIP Lookup Engine
GEOIP_CACHE = {}
GEOIP_PENDING = set()
GEOIP_LOCK = threading.Lock()
GEOIP_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="GeoIPWorker")

def _fetch_geoip_async(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,city,isp,org', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                city = data.get('city', '')
                country = data.get('country', '')
                isp = data.get('isp', '')
                location_str = f"{city}, {country}" if city and country else (country or city or 'External')
                if isp:
                    location_str += f" ({isp})"
                with GEOIP_LOCK:
                    GEOIP_CACHE[ip] = location_str
                return
        with GEOIP_LOCK:
            GEOIP_CACHE[ip] = 'External'
    except Exception:
        with GEOIP_LOCK:
            GEOIP_CACHE[ip] = 'Unknown Location'
    finally:
        with GEOIP_LOCK:
            GEOIP_PENDING.discard(ip)

def get_geoip(ip):
    if is_private_ip(ip):
        return 'Local / Internal Network'
    
    with GEOIP_LOCK:
        if ip in GEOIP_CACHE:
            return GEOIP_CACHE[ip]
        if ip not in GEOIP_PENDING:
            GEOIP_PENDING.add(ip)
            GEOIP_EXECUTOR.submit(_fetch_geoip_async, ip)
        return 'Resolving Location...'

# System Process Whitelist for Privilege Alert Filter
SYSTEM_WHITELIST = {
    'sshd', 'nginx', 'apache2', 'system', 'svchost.exe', 'system idle process',
    'lsass.exe', 'services.exe', 'smss.exe', 'spoolsv.exe', 'csrss.exe',
    'wininit.exe', 'winlogon.exe', 'explorer.exe', 'sqlservr.exe', 'mysqld.exe',
    'postgres.exe', 'httpd.exe', 'system / protected', 'system idle / kernel',
    'alg.exe', 'dashost.exe', 'sihost.exe', 'searchindexer.exe', 'comppkgsrv.exe'
}

# Known Malicious / Backdoor Port Rules
KNOWN_THREAT_PORTS = {
    4444: 'Metasploit / Reverse Shell Port',
    6667: 'IRC Botnet Control Channel',
    31337: 'Back Orifice Trojan Port',
    1337: 'LEET Backdoor Listening Port',
    5555: 'Android ADB Debug Exposure',
    8888: 'Unsecured Alt HTTP Control Server',
    9999: 'Raw Socket Backdoor Connection'
}

# Data Retention Policy (Keep last 7 days)
def prune_old_records(db_manager):
    try:
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        db_manager.execute('DELETE FROM port_activity WHERE timestamp < ?', (cutoff,))
        db_manager.execute('DELETE FROM process_inventory WHERE timestamp < ?', (cutoff,))
    except Exception as e:
        logging.error(f"Error pruning database records: {e}")

# Data Collection Engine
def collect_data(db_manager):
    try:
        timestamp = datetime.now().isoformat()

        try:
            connections = psutil.net_connections(kind='inet')
        except (psutil.AccessDenied, PermissionError):
            try:
                connections = psutil.net_connections(kind='tcp') + psutil.net_connections(kind='udp')
            except Exception:
                connections = []

        socket_records = []
        process_cache = {}
        alerts_to_log = []

        for conn in connections:
            if not conn.laddr:
                continue

            pid = conn.pid if conn.pid else 0
            proc_info = process_cache.get(pid)

            if not proc_info:
                proc_info = get_process_info(pid)
                process_cache[pid] = proc_info

            port = conn.laddr.port
            proc_info['ports'].add(port)

            remote_ip = conn.raddr.ip if conn.raddr else ''
            remote_port = conn.raddr.port if conn.raddr else 0
            location = get_geoip(remote_ip)
            protocol = 'TCP' if conn.type == 1 else 'UDP'
            status = conn.status if conn.status else 'ACTIVE'

            socket_records.append((
                timestamp, pid, proc_info['name'], proc_info['exe'],
                port, protocol, remote_ip, remote_port, status, location
            ))

            # Threat Engine Inspections
            # Rule 1: Known Threat / Backdoor Ports
            if port in KNOWN_THREAT_PORTS:
                alerts_to_log.append((
                    timestamp, 'CRITICAL', pid, proc_info['name'], port, remote_ip,
                    'Known Threat Port', f"Socket bound to {KNOWN_THREAT_PORTS[port]} (Port {port})"
                ))

            # Rule 2: Non-whitelisted Low Ports (<1024) listening
            elif port < 1024 and status in ('LISTEN', 'LISTENING') and proc_info['name'].lower() not in SYSTEM_WHITELIST:
                alerts_to_log.append((
                    timestamp, 'CRITICAL', pid, proc_info['name'], port, remote_ip,
                    'Privileged Port Binding', f"Non-system process '{proc_info['name']}' bound to restricted port {port}"
                ))

            # Rule 3: Suspicious Outbound Connection to Foreign IP
            elif status == 'ESTABLISHED' and remote_ip and not is_private_ip(remote_ip) and remote_port not in (80, 443, 8080, 8443, 5228, 5222, 5223, 53, 22, 587, 465, 993, 995, 3389, 8000):
                alerts_to_log.append((
                    timestamp, 'WARNING', pid, proc_info['name'], port, remote_ip,
                    'Unusual Remote Connection', f"Active outbound connection to {remote_ip}:{remote_port} ({location})"
                ))

        # Batch Insert Socket Snapshot
        if socket_records:
            db_manager.execute_many('''
                INSERT INTO port_activity
                (timestamp, pid, process_name, exe_path, port, protocol, remote_ip, remote_port, status, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', socket_records)

        # Batch Insert Process Telemetry Inventory
        proc_records = []
        for pid, info in process_cache.items():
            proc_records.append((
                timestamp, pid, info['name'], info['exe'],
                info['username'], round(info['cpu'], 1), round(info['mem'], 1), len(info['ports'])
            ))
        
        if proc_records:
            db_manager.execute_many('''
                INSERT INTO process_inventory
                (timestamp, pid, process_name, exe_path, username, cpu_percent, memory_mb, open_ports)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', proc_records)

        # Process Security Alerts (Deduplicated)
        for alert in alerts_to_log:
            existing = db_manager.execute('''
                SELECT id FROM security_alerts
                WHERE pid = ? AND port = ? AND rule_name = ? AND status = 'ACTIVE'
            ''', (alert[2], alert[4], alert[6]), fetch=True)

            if not existing:
                db_manager.execute('''
                    INSERT INTO security_alerts
                    (timestamp, severity, pid, process_name, port, remote_ip, rule_name, description, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                ''', alert)

                # Write to security log file
                alert_logger.info(f"[{alert[1]}] {alert[0]} - {alert[6]}: {alert[7]} (PID: {alert[2]})")

        # Maintenance Cleanup
        prune_old_records(db_manager)
    except Exception as e:
        logging.error(f"Error in collect_data: {e}")

# Background Collection Loop
def data_collection_thread(db_manager):
    while True:
        collect_data(db_manager)
        time.sleep(5)

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    try:
        db_manager = get_db_manager()
        port_filter = request.args.get('port', '').strip()
        process_filter = request.args.get('process', '').strip()
        status_filter = request.args.get('status', '').strip()
        protocol_filter = request.args.get('protocol', '').strip()

        query = '''
            SELECT pid, process_name, exe_path, port, protocol, remote_ip, remote_port, status, location
            FROM port_activity
            WHERE timestamp = (SELECT MAX(timestamp) FROM port_activity)
        '''
        params = []

        if port_filter and port_filter.isdigit():
            query += ' AND port = ?'
            params.append(int(port_filter))

        if process_filter:
            query += ' AND (process_name LIKE ? OR exe_path LIKE ?)'
            params.append(f'%{process_filter}%')
            params.append(f'%{process_filter}%')

        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter.upper())

        if protocol_filter:
            query += ' AND protocol = ?'
            params.append(protocol_filter.upper())

        snapshot = db_manager.execute(query, params, fetch=True) or []

        # Get Chronological Timeline for Chart (Bounded to last 2 hours for sub-millisecond query performance)
        cutoff_time = (datetime.now() - timedelta(hours=2)).isoformat()
        timeline = db_manager.execute('''
            SELECT timestamp, COUNT(DISTINCT port) as port_count
            FROM port_activity
            WHERE timestamp >= ?
            GROUP BY timestamp
            ORDER BY timestamp DESC
            LIMIT 40
        ''', (cutoff_time,), fetch=True) or []

        timeline_chronological = list(reversed(timeline))

        # Get Active Security Alerts Count
        active_alerts = db_manager.execute('''
            SELECT COUNT(*) as count FROM security_alerts WHERE status = 'ACTIVE'
        ''', fetch=True)
        alerts_count = active_alerts[0]['count'] if active_alerts else 0

        # System Resource Metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()

        return jsonify({
            'snapshot': snapshot,
            'timeline': timeline_chronological,
            'metrics': {
                'total_ports': len(snapshot),
                'established': sum(1 for row in snapshot if row['status'] == 'ESTABLISHED'),
                'listening': sum(1 for row in snapshot if row['status'] in ('LISTEN', 'LISTENING')),
                'processes': len(set(row['pid'] for row in snapshot)),
                'active_alerts': alerts_count,
                'system_cpu': cpu_usage,
                'system_ram': mem.percent
            }
        })
    except Exception as e:
        logging.error(f"Error in get_data API: {e}")
        return jsonify({'snapshot': [], 'timeline': [], 'metrics': {}})

@app.route('/api/alerts')
def get_alerts():
    try:
        db_manager = get_db_manager()
        status = request.args.get('status', 'ACTIVE')
        alerts = db_manager.execute('''
            SELECT id, timestamp, severity, pid, process_name, port, remote_ip, rule_name, description, status
            FROM security_alerts
            WHERE status = ?
            ORDER BY id DESC
            LIMIT 100
        ''', (status,), fetch=True) or []
        return jsonify({'alerts': alerts})
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return jsonify({'alerts': []})

@app.route('/api/alerts/acknowledge/<int:alert_id>', methods=['POST'])
def acknowledge_alert(alert_id):
    try:
        db_manager = get_db_manager()
        db_manager.execute('''
            UPDATE security_alerts SET status = 'ACKNOWLEDGED' WHERE id = ?
        ''', (alert_id,))
        return jsonify({'success': True, 'message': f'Alert {alert_id} acknowledged.'})
    except Exception as e:
        logging.error(f"Error acknowledging alert: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/processes')
def get_processes():
    try:
        db_manager = get_db_manager()
        processes = db_manager.execute('''
            SELECT pid, process_name, exe_path, username, cpu_percent, memory_mb, open_ports
            FROM process_inventory
            WHERE timestamp = (SELECT MAX(timestamp) FROM process_inventory)
            ORDER BY open_ports DESC, cpu_percent DESC
        ''', fetch=True) or []
        return jsonify({'processes': processes})
    except Exception as e:
        logging.error(f"Error fetching processes: {e}")
        return jsonify({'processes': []})

@app.route('/api/export/<format>')
def export_logs(format):
    try:
        db_manager = get_db_manager()
        data = db_manager.execute('''
            SELECT timestamp, pid, process_name, exe_path, port, protocol, remote_ip, remote_port, status, location
            FROM port_activity
            ORDER BY id DESC
            LIMIT 5000
        ''', fetch=True) or []

        if format.lower() == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Timestamp', 'PID', 'Process Name', 'Executable Path', 'Port', 'Protocol', 'Remote IP', 'Remote Port', 'Status', 'Location'])
            for row in data:
                writer.writerow([
                    row['timestamp'], row['pid'], row['process_name'], row['exe_path'],
                    row['port'], row['protocol'], row['remote_ip'], row['remote_port'],
                    row['status'], row['location']
                ])
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name='enterprise_port_activity.csv'
            )
        elif format.lower() == 'json':
            return Response(json.dumps(data, indent=2), mimetype='application/json')
        else:
            return jsonify({'error': 'Invalid export format. Use csv or json'}), 400
    except Exception as e:
        logging.error(f"Error exporting logs: {e}")
        return jsonify({'error': 'Export failed'}), 500

def start_application(db_path=None):
    global DB_PATH
    if db_path:
        DB_PATH = db_path

    os.makedirs('templates', exist_ok=True)
    db_manager = get_db_manager()
    init_db(db_manager)

    # Start background collector thread once
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        t = threading.Thread(target=data_collection_thread, args=(db_manager,), daemon=True)
        t.name = "DataCollectorThread"
        t.start()

if __name__ == '__main__':
    start_application()
    print("Starting Live Production Server at http://127.0.0.1:5000")
    
    try:
        from waitress import serve
        print("Running with Waitress Production WSGI Server...")
        serve(app, host='127.0.0.1', port=5000, threads=8)
    except ImportError:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)