# ⚡ **Process Visualizer** 🛡️

A high-performance, real-time network port, process telemetry, and threat inspection engine built for Windows systems.

---

## 👨‍💻 **Author & Contact**

* **Developer**: Chandu Gollavilli
* **Email**: [chandugollavilli@gmail.com](mailto:chandugollavilli@gmail.com)
* **LinkedIn**: [https://www.linkedin.com/in/chandragollavilli/](https://www.linkedin.com/in/chandragollavilli/)
* **Repository**: [https://github.com/chandugollavilli/PortProcessVisualizer](https://github.com/chandugollavilli/PortProcessVisualizer)

---

## 📑 **Table of Contents**
- [🌟 Key Features](#-key-features)
- [💻 System Architecture](#-system-architecture)
- [🛠 Installation & Setup](#-installation--setup)
- [🚀 Production Execution](#-production-execution)
- [🔌 REST API Reference](#-rest-api-reference)
- [🛡️ Threat Detection Engine](#%EF%B8%8F-threat-detection-engine)
- [📜 License](#-license)

---

## 🌟 **Key Features**

* ⚡ **Live Real-Time Monitoring**: Continuously scans active system sockets, network connections, and running processes using `psutil`.
* 🖤 **Black & Hacker Grey Dashboard**: Sleek, high-contrast dark theme with matrix green & neon cyan accents, custom badges, and live telemetry cards.
* 🛡️ **Automated Threat Detection Engine**: Automatically flags restricted low-port bindings (<1024), known backdoor/trojan ports (4444, 6667, 31337, etc.), and suspicious foreign connections.
* 💾 **SQLite WAL High-Concurrency Storage**: Utilizes Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) with thread locking and automated 7-day data retention pruning.
* 🌐 **Multi-Threaded Production WSGI Engine**: Powered by **Waitress** WSGI server (`threads=8`) for multi-threaded Windows enterprise deployment.
* 📍 **Smart LRU GeoIP Lookup**: Automatically classifies local/private subnets (`127.0.0.1`, `10.x.x.x`, `192.168.x.x`, `172.16-31.x.x`) locally and caches external IP lookups via `ip-api.com`.
* 📤 **Filtered Data Export**: Download live activity logs in standard **CSV** or **JSON** formats.

---

## 💻 **System Architecture**

```text
[ Windows Network Sockets & Processes ]
                  │
                  ▼ (psutil telemetry scan every 5s)
     ┌──────────────────────────┐
     │  port_process_visualizer │ ──► Threats Engine (Alerts)
     └──────────────────────────┘
                  │
                  ▼ (SQLite WAL Engine - port_activity.db)
     ┌──────────────────────────┐
     │ Waitress Production WSGI │
     └──────────────────────────┘
                  │
                  ▼ (REST APIs)
     ┌──────────────────────────┐
     │  Process Visualizer UI   │ ──► Black & Hacker Grey Dashboard
     └──────────────────────────┘
```

---

## 🛠 **Installation & Setup**

### Prerequisites:
- **Operating System**: Windows 10, Windows 11, or Windows Server 2016+
- **Python**: Python 3.8 or higher
- **Permissions**: Administrator privileges (recommended for complete socket & process inspection)

### Installation Steps:

```powershell
# 1. Clone the repository
git clone https://github.com/chandugollavilli/PortProcessVisualizer.git
cd PortProcessVisualizer

# 2. Install production Python dependencies
pip install psutil flask requests waitress
```

---

## 🚀 **Production Execution**

### Run in Live Production Mode:
```powershell
python run_production.py
```

Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔌 **REST API Reference**

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/data` | `GET` | Fetches live active sockets, CPU/RAM metrics, and timeline data. Query params: `port`, `process`, `status`, `protocol`. |
| `/api/alerts` | `GET` | Returns active security threat alerts. Filter by `status` (`ACTIVE` or `ACKNOWLEDGED`). |
| `/api/alerts/acknowledge/<id>` | `POST` | Acknowledges and dismisses a security threat incident. |
| `/api/processes` | `GET` | Retrieves full running process inventory with PID, EXE path, username, CPU %, RAM MB, and socket counts. |
| `/api/export/csv` | `GET` | Exports socket activity logs to CSV format. |
| `/api/export/json` | `GET` | Exports socket activity logs to JSON format. |

---

## 🛡️ **Threat Detection Engine**

The threat engine automatically inspects network traffic and triggers alert incidents for:
1. **Privileged Port Binding (`CRITICAL`)**: Non-system process binding to ports < 1024.
2. **Known Threat Port (`CRITICAL`)**: Socket binding to known reverse shell/trojan ports (e.g., `4444` Metasploit, `6667` IRC botnet, `31337` Back Orifice, `1337` LEET, `5555` ADB debug).
3. **Unusual Remote Connection (`WARNING`)**: Active outbound connection (`ESTABLISHED`) to non-standard remote IP addresses.

---

## 📜 **License**

Licensed under the [MIT License](LICENSE).

---

### Built by **Chandu Gollavilli** &bull; [LinkedIn](https://www.linkedin.com/in/chandragollavilli/) &bull; [Email](mailto:chandugollavilli@gmail.com)
