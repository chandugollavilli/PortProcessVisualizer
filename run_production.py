"""
Production Launcher for Process Visualizer.
Uses Waitress multi-threaded WSGI server for cross-platform production deployment.
"""

import sys
import os
import logging
from waitress import serve
from port_process_visualizer import app, start_application

if __name__ == '__main__':
    print("==========================================================")
    print(" Process Visualizer - Production Live Edition")
    print("==========================================================")
    print("  Server Address: http://127.0.0.1:5000")
    print("  Database Mode: SQLite WAL Mode (High Concurrency)")
    print("  WSGI Engine:   Waitress Production Server (8 Worker Threads)")
    print("  Logging:       app.log & alerts.log")
    print("==========================================================")
    
    start_application()
    
    try:
        serve(app, host='127.0.0.1', port=5000, threads=8)
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Production server crash: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1)
