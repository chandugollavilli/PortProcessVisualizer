<div align="center">

# ⚡ Process Visualizer 🛡️

### **Real-Time Cross-Platform Network Socket & Process Intelligence Engine**

[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-cyan.svg)](#-cross-platform-support)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](#-contributing)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](#-production-deployment)

---

[Key Features](#-key-features) &bull; [Quick Start](#-quick-start) &bull; [Architecture](#-architecture) &bull; [API Docs](#-rest-api-reference) &bull; [Contributing](#-contributing) &bull; [Author](#-author--contact)

</div>

---

## 📖 About The Project

**Process Visualizer** is an open-source, high-performance network security and process inspection tool engineered for **Windows** and **Linux** environments.

It bridges low-level system socket telemetry with real-time threat intelligence, providing security analysts, network engineers, and system administrators with a high-contrast **Black & Hacker Grey Operations Dashboard**.

---

## ✨ Key Features

* ⚡ **Live Real-Time Telemetry**: Continuously tracks active network connections, listening ports, established sockets, and running processes using `psutil`.
* 🖤 **Black & Hacker Grey Dashboard**: Sleek, high-contrast dark theme with matrix green (`#10b981`) and neon cyan (`#06b6d4`) visual indicators.
* 🛡️ **Automated Threat Detection Engine**: Automatically flags restricted low-port bindings (<1024), known backdoor/trojan ports (e.g., 4444, 6667, 31337, 1337, 5555), and foreign outbound connections.
* 💾 **SQLite WAL High-Concurrency Storage**: Utilizes Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) with thread locking and automated 7-day data retention pruning.
* 🌐 **Multi-Threaded Production WSGI Engine**: Powered by **Waitress** WSGI server (`threads=8`) out-of-the-box for enterprise deployment.
* 📍 **Smart LRU GeoIP Lookup**: Classifies local/private subnets (`127.0.0.1`, `10.x.x.x`, `192.168.x.x`, `172.16-31.x.x`) instantly and caches external IP locations via `ip-api.com`.
* 📤 **Filtered Data Export**: Download socket activity logs in standard **CSV** or **JSON** formats.

---

## 🏗 Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 System Sockets & Telemetry                  │
│             (Windows psutil / Linux /proc /net)             │
└──────────────────────────────┬──────────────────────────────┘
                               │ (5s Telemetry Scan)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            Process Visualizer Core Backend                  │
│       (Threat Engine, Alert Loggers & LRU GeoIP)            │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Atomic WAL Transactions)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           SQLite WAL Database (port_activity.db)            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│        Waitress WSGI Production Engine (8 Threads)          │
└──────────────────────────────┬──────────────────────────────┘
                               │ (REST JSON APIs)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│        Process Visualizer Hacker Dashboard (UI)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 Cross-Platform Support

| Feature | Windows | Linux | Requirements |
| :--- | :---: | :---: | :--- |
| **Socket Telemetry** | ✅ | ✅ | Admin Prompt (Windows) / `sudo` (Linux) for complete PID resolution |
| **WSGI Server** | ✅ (Waitress) | ✅ (Waitress / Gunicorn) | Multi-threaded Waitress WSGI included |
| **Database Engine** | ✅ | ✅ | SQLite WAL mode works natively on all OSes |
| **Daemon Whitelist** | ✅ | ✅ | Whitelists daemons (`sshd`, `nginx`, `apache2`) and services (`svchost.exe`, `lsass.exe`) |

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python**: 3.8 or higher
- **Permissions**: Administrator privileges (Windows Elevated PowerShell) or Root (`sudo` on Linux)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/chandugollavilli/PortProcessVisualizer.git
cd PortProcessVisualizer

# Install dependencies
pip install -r requirements.txt   # or: pip install psutil flask requests waitress
```

### 3. Run Production Server

#### Windows (Elevated PowerShell):
```powershell
python run_production.py
```

#### Linux (Terminal):
```bash
sudo python3 run_production.py
```

Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔌 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/data` | `GET` | Fetches active sockets, CPU/RAM metrics, and timeline data. Query params: `port`, `process`, `status`, `protocol`. |
| `/api/alerts` | `GET` | Returns active security threat alerts. Filter by `status` (`ACTIVE` or `ACKNOWLEDGED`). |
| `/api/alerts/acknowledge/<id>` | `POST` | Acknowledges and dismisses a security threat incident. |
| `/api/processes` | `GET` | Retrieves full running process inventory with PID, EXE path, username, CPU %, RAM MB, and socket counts. |
| `/api/export/csv` | `GET` | Exports socket activity logs to CSV format. |
| `/api/export/json` | `GET` | Exports socket activity logs to JSON format. |

---

## 🛡️ Threat Detection Rules

The automated security threat engine scans system sockets every tick and triggers incidents for:
1. **Privileged Port Binding (`CRITICAL`)**: Non-system process binding to restricted ports below 1024.
2. **Known Threat Port (`CRITICAL`)**: Socket binding to known reverse shell/trojan ports (e.g., `4444` Metasploit, `6667` IRC botnet, `31337` Back Orifice, `1337` LEET, `5555` ADB debug).
3. **Unusual Remote Connection (`WARNING`)**: Active outbound connection (`ESTABLISHED`) to non-standard remote IP addresses.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**!

### How to Contribute:

1. **Fork the Project** (`https://github.com/chandugollavilli/PortProcessVisualizer/fork`)
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.

---

## 👨‍💻 Author & Contact

**Chandu Gollavilli**

* **Email**: [chandugollavilli@gmail.com](mailto:chandugollavilli@gmail.com)
* **LinkedIn**: [https://www.linkedin.com/in/chandragollavilli/](https://www.linkedin.com/in/chandragollavilli/)
* **Project Link**: [https://github.com/chandugollavilli/PortProcessVisualizer](https://github.com/chandugollavilli/PortProcessVisualizer)
