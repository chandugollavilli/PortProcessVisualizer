Here’s an enhanced and more visually engaging version of your **Port and Process Activity Visualizer** project README. It maintains the core information but improves formatting, readability, and appeal:

---

# 🔍 **Port and Process Activity Visualizer** 🚀

A sleek, real-time monitoring tool for network ports and system processes on **Windows**.

Designed for **network administrators**, **security analysts**, and **developers**, this intuitive tool helps visualize, filter, and analyze port activity via a modern web interface.

---

## 📑 **Table of Contents**

* [✨ Features](#-features)
* [📸 Screenshots](#-screenshots)
* [🛠 Installation](#-installation)
* [🚀 Usage](#-usage)
* [🧪 Testing](#-testing)
* [🛡️ Troubleshooting](#-troubleshooting)
* [🤝 Contributing](#-contributing)
* [📜 License](#-license)
* [📬 Contact](#-contact)

---

## ✨ **Features**

* 🔄 **Real-Time Monitoring**
  Updates every 10 seconds using `psutil` to track active ports and running processes.
* 🌐 **Web-Based UI**
  Clean, responsive interface with data table and dynamic timeline chart.
* 🔍 **Smart Filters**
  Filter by specific ports (e.g., `8000`) or process names (e.g., `python.exe`).
* 📍 **GeoIP Lookup**
  Visualize remote IP locations (City & Country) via `ip-api.com`.
* 📤 **Export Logs**
  Download session data as **CSV** or **JSON** for further analysis.
* 🚨 **Security Alerts**
  Detects and logs suspicious behavior (e.g., non-standard apps on ports < 1024).
* 💾 **Thread-Safe Storage**
  SQLite-backed data persistence with robust access handling.
* 🪟 **Optimized for Windows 10/11**
  Excludes core system processes like `svchost.exe`.

---

## 📸 **Screenshots**

> Visual previews of the dashboard, timeline chart, and filter/search functionality.

---

## 🛠 **Installation**

> Follow these simple steps to get started:

### ✅ Prerequisites:

* Windows 10 or 11
* Python 3.8+
* Git (optional)
* Internet access (for GeoIP)
* Admin privileges

### 🔧 Setup:

```powershell
mkdir C:\Temp\ports
cd C:\Temp\ports
icacls C:\Temp\ports /grant Everyone:F
git clone https://github.com/chandugollavilli/PortProcessVisualizer
cd PortProcessVisualizer
pip install psutil flask requests
```

Ensure these files are present:

* `port_process_visualizer.py`
* `SOP_Port_Process_Visualizer.md`
* `templates/index.html`

---

## 🚀 **Usage**

### ▶️ Run the Application:

```powershell
cd C:\Temp\ports
python port_process_visualizer.py
```

Visit [http://localhost:5000](http://localhost:5000) to explore the dashboard.

### 🧪 Generate Test Data:

```bash
python -m http.server 8000
# View 'python.exe' on port 8000 in the UI
taskkill /IM python.exe /F
```

### 🚨 Monitor Alerts:

```bash
python -m http.server 80
type alerts.log
```

---

## 🧪 **Testing**

### 🔍 Database Structure:

```python
import sqlite3
conn = sqlite3.connect('port_activity.db')
c = conn.cursor()
c.execute("PRAGMA table_info(port_activity)")
print(c.fetchall())
conn.close()
```

Expected columns: `timestamp`, `pid`, `process_name`, `port`, `protocol`, `remote_ip`, `status`, `location`

### ✅ UI Filters:

* Filter by `8000` or `python`
* Results update dynamically

### 🌍 GeoIP Test:

```bash
curl http://example.com
```

Expected location (e.g., “Mumbai, India”) in the UI.

### 📤 Export:

Use UI buttons to download CSV or JSON.

### 🚨 Alert Validation:

Check `alerts.log` after running a low-port process.

---

## 🛡️ **Troubleshooting**

| Issue                | Solution                                    |
| -------------------- | ------------------------------------------- |
| `database is locked` | Delete `port_activity.db` and restart       |
| UI not updating      | Check browser console (F12) & `/api/data`   |
| GeoIP not showing    | Test: `curl http://ip-api.com/json/8.8.8.8` |
| General issues       | Use Admin PowerShell, verify folder access  |

📘 Refer to **Section 5.4** of `SOP_Port_Process_Visualizer.md` for advanced fixes.

---

## 🤝 **Contributing**

We welcome your contributions!
To add features or fix issues:

```bash
# Fork and clone
git checkout -b feature/your-feature
# After edits
git commit -m "Add your feature"
git push origin feature/your-feature
```

➡️ Submit a Pull Request and follow the project's coding style.

---

## 📜 License

Licensed under the [MIT License](LICENSE).

---

## 📬 Contact

💬 Open a GitHub issue or email the maintainer: **[chandugollavilli66@gmail.com](mailto:chandugollavilli66@gmail.com)**
📎 Include your `app.log` and exact steps to reproduce any issues.

---

### Built with ❤️ using Python, Flask & SQLite

> Real-time insights. Secure systems. Simplified.
> Happy monitoring! 🧠🔐📊

---

