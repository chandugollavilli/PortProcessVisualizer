# 🛡️ Process Visualizer - Technical Project Documentation

---

## 📑 Table of Contents
- [1. Executive Summary](#1-executive-summary)
- [2. System Architecture & Component Interaction](#2-system-architecture--component-interaction)
- [3. Database Schema & WAL Concurrency Engine](#3-database-schema--wal-concurrency-engine)
- [4. Security Threat Detection Engine](#4-security-threat-detection-engine)
- [5. Process & Resource Telemetry Engine](#5-process--resource-telemetry-engine)
- [6. RESTful API Specifications](#6-restful-api-specifications)
- [7. Frontend UI & Design System](#7-frontend-ui--design-system)
- [8. Deployment & Operational Maintenance](#8-deployment--operational-maintenance)

---

## 1. Executive Summary

**Process Visualizer** is an open-source, enterprise-grade, real-time network port, process telemetry, and security incident inspection platform designed for **Windows** and **Linux** environments.

It bridges OS-level network socket tracking (`psutil`) with lightweight threat intelligence rules, delivering continuous visibility into listening ports, active outbound TCP/UDP connections, process resource usage (CPU %, Memory MB), and suspicious network activity via a high-contrast **Black & Hacker Grey Operations Dashboard**.

---

## 2. System Architecture & Component Interaction

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Windows / Linux System Sockets                       │
│                     (psutil.net_connections)                           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (5s Telemetry Collector Loop)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                Process Visualizer Core Engine                          │
│                                                                        │
│   ├── Socket Collector Thread      ├── GeoIP LRU Cache Engine          │
│   ├── Process Telemetry Mapper     └── Security Threat Rules Inspector │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Atomic WAL SQL Transactions)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 SQLite WAL Database (port_activity.db)                 │
│              (port_activity, security_alerts, process_inventory)       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              Waitress WSGI Production Server (8 Threads)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (REST JSON Endpoints)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Process Visualizer Hacker Dashboard UI                   │
│         (Socket Inspector, Threat Center, Process Manager, Analytics)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema & WAL Concurrency Engine

The application utilizes **SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`)** combined with thread locking (`threading.Lock()`) to allow high-frequency background write transactions while serving concurrent UI read queries without locking errors.

### Schema Definitions:

#### Table 1: `port_activity` (Socket Snapshots)
```sql
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
);
```

#### Table 2: `security_alerts` (Security Incident Alerts)
```sql
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
);
```

#### Table 3: `process_inventory` (Process Telemetry)
```sql
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
);
```

---

## 4. Security Threat Detection Engine

The automated threat inspection engine evaluates every socket connection against three threat rules:

1. **Privileged Low-Port Binding (`CRITICAL`)**: Flags non-system processes binding to restricted listening ports below 1024.
2. **Known Threat Port Binding (`CRITICAL`)**: Flags sockets binding to known backdoor, reverse shell, or malware ports:
   - Port `4444`: Metasploit Reverse Shell
   - Port `6667`: IRC Botnet Control
   - Port `31337`: Back Orifice Trojan
   - Port `1337`: LEET Backdoor
   - Port `5555`: Unsecured Android ADB Debug
3. **Unusual Foreign Outbound Connection (`WARNING`)**: Flags active outbound connections (`ESTABLISHED`) to non-standard remote ports outside standard HTTP/HTTPS/8080.

---

## 5. Process & Resource Telemetry Engine

The background collector inspects system processes every 5 seconds to capture:
- **PID**: Process Identification Number
- **Process Name & Executable Path**: `psutil.Process(pid).exe()`
- **User Account**: Operating system account running the process
- **CPU & Memory Metrics**: `cpu_percent()` and `memory_info().rss` in MB
- **Open Sockets Count**: Aggregate active ports mapped per process

---

## 6. RESTful API Specifications

| Endpoint | Method | Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/data` | `GET` | `port`, `process`, `status`, `protocol` | Returns current active socket snapshot, overall CPU/RAM metrics, and historical timeline. |
| `/api/alerts` | `GET` | `status` (`ACTIVE`/`ACKNOWLEDGED`) | Returns security threat alert incidents. |
| `/api/alerts/acknowledge/<id>` | `POST` | `alert_id` (path variable) | Acknowledges and resolves a specific security alert. |
| `/api/processes` | `GET` | None | Returns process inventory with resource utilization and socket counts. |
| `/api/export/csv` | `GET` | None | Downloads current socket activity log as a CSV file. |
| `/api/export/json` | `GET` | None | Exports current socket activity log as a JSON array. |

---

## 7. Frontend UI & Design System

The frontend is implemented in vanilla HTML5, CSS3, and ES6 JavaScript with Chart.js and FontAwesome.

- **Theme Palette**: Deep Matte Black (`#000000`), Dark Charcoal Grey (`#111111`), Dark Border (`#222222`), Matrix Green (`#10b981`), Neon Cyan (`#06b6d4`), Crimson (`#f43f5e`).
- **Typography**: `Inter` font for UI elements & `JetBrains Mono` for PIDs, IP addresses, ports, and code paths.
- **Dynamic Telemetry Updates**: Polling loop fetches live socket snapshots, process lists, metrics, and threat alerts every 5 seconds without full page refreshes.

---

## 8. Deployment & Operational Maintenance

### Launching Production Server:

#### Windows:
```powershell
python run_production.py
```

#### Linux:
```bash
sudo python3 run_production.py
```

### Server Specifications:
- **Host**: `127.0.0.1` (configurable)
- **Port**: `5000` (configurable)
- **WSGI Engine**: Waitress (8 worker threads)
- **Log Files**: `app.log` (operational events) & `alerts.log` (security incidents)
