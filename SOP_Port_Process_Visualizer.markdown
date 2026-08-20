# Standard Operating Procedure (SOP) for Enterprise Port and Process Activity Visualizer

## 1. Purpose
This Standard Operating Procedure (SOP) outlines the operational procedures to install, configure, run, test, troubleshoot, and maintain the Enterprise Port and Process Activity Visualizer on Windows systems. The application provides real-time corporate network port monitoring, process telemetry, threat rule detection, incident alert acknowledgement, and log exports via a multi-tab web dashboard.

## 2. Scope
This SOP applies to system administrators, security operations analysts, and developers deploying the application in live Windows enterprise environments (Windows 10/11, Windows Server 2016+).

## 3. Responsibilities
- **Security Operations / Administrator**: Deploys the application, monitors threat alerts, acknowledges security incidents, and manages log retention.
- **Developer**: Maintains backend API logic, SQLite WAL thread-safety, and frontend dashboard telemetry.
- **System Admin**: Configures Waitress WSGI production service, network permissions, and firewalls.

## 4. Prerequisites
- **Operating System**: Windows 10, 11, or Windows Server 2016+.
- **Software**: Python 3.8+, pip, Web browser (Edge, Chrome, Firefox).
- **Dependencies**: `psutil`, `flask`, `requests`, `waitress`.
- **Permissions**: Administrator privileges (elevated command prompt) to capture all network sockets and process paths.

## 5. Procedure

### 5.1 Installation
1. Navigate to working directory:
   ```powershell
   cd C:\Users\FCI\Desktop\PortProcessVisualizer
   ```
2. Install production Python packages:
   ```powershell
   pip install psutil flask requests waitress
   ```
3. Verify installed dependencies:
   ```powershell
   pip list
   ```

### 5.2 Running the Production Application
1. Start the production Waitress server:
   ```powershell
   python run_production.py
   ```
   - Expected Output:
     ```text
     ==========================================================
      Port & Process Visualizer - Enterprise Live Edition
     ==========================================================
       Server Address: http://127.0.0.1:5000
       Database Mode: SQLite WAL Mode (High Concurrency)
       WSGI Engine:   Waitress Production Server (8 Worker Threads)
       Logging:       app.log & alerts.log
     ==========================================================
     ```

2. Open the Dashboard:
   - Navigate to `http://127.0.0.1:5000` in any web browser.

### 5.3 Core Features & Navigation
1. **Socket Inspector Tab**: Live network socket table with process names, executable paths, local ports, protocols, remote addresses, and GeoIP location tags.
2. **Threat Center Tab**: Real-time security incident alerts feed featuring rule descriptions and one-click alert acknowledgement.
3. **Process Manager Tab**: Resource telemetry listing PID, User Account, Executable Path, CPU %, Memory Usage (MB), and bound open port counts.
4. **Traffic Analytics Tab**: Time-series active socket chart and TCP vs UDP protocol distribution doughnut chart.
5. **Log Exports**: Click "Export CSV" or "Export JSON" to download socket logs.

### 5.4 Troubleshooting & Maintenance
- **Database Lock Errors**: The application uses SQLite WAL Mode (`PRAGMA journal_mode=WAL;`) with thread locking to eliminate `database is locked` issues.
- **GeoIP Lookup Optimization**: Private/local IPs (`127.0.0.1`, `10.x.x.x`, `192.168.x.x`) are resolved locally without making external HTTP requests.
- **Log Inspection**: Inspect `app.log` and `alerts.log` for operational telemetry and security incident logs.

---

## Appendix A: Production Application Code (`port_process_visualizer.py`)

```python
import psutil
import sqlite3
import time
from datetime import datetime, timedelta
import threading
from flask import Flask, render_template, send_file, request, jsonify, Response
import json
import logging
import os
import requests
import csv
import io
import functools

# Configure production logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s'
)

app = Flask(__name__)

# Global Database Path configuration
DB_PATH = 'port_activity.db'

# Enterprise Thread-Safe Database Manager with WAL Mode
class DatabaseManager:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DB_PATH
        self.lock = threading.Lock()
        self._configure_wal()

    def _configure_wal(self):
        """Configure SQLite WAL mode for high concurrency concurrent reads/writes."""
        try:
            with self.lock:
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
                with self.lock:
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
                with self.lock:
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

def get_db_manager():
    return DatabaseManager(DB_PATH)

def init_db(db_manager):
    try:
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

        result = db_manager.execute('''PRAGMA table_info(port_activity)''', fetch=True) or []
        columns = [row['name'] for row in result]
        if 'exe_path' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN exe_path TEXT')
        if 'remote_port' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN remote_port INTEGER')
        if 'location' not in columns:
            db_manager.execute('ALTER TABLE port_activity ADD COLUMN location TEXT')

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

        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_timestamp ON port_activity(timestamp);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_port ON port_activity(port);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_pa_proc ON port_activity(process_name);')
        db_manager.execute('CREATE INDEX IF NOT EXISTS idx_alerts_status ON security_alerts(status);')
    except Exception as e:
        logging.error(f"Error initializing enterprise database: {e}")
        raise

if __name__ == '__main__':
    start_application()
    print("Starting Live Production Server at http://127.0.0.1:5000")
    try:
        from waitress import serve
        serve(app, host='127.0.0.1', port=5000, threads=8)
    except ImportError:
        app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
```