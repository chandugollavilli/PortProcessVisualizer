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
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    threads = int(os.environ.get('THREADS', '8'))

    print("==========================================================")
    print(" Process Visualizer - Production Live Edition")
    print("==========================================================")
    print(f"  Server Address: http://{host}:{port}")
    print("  Database Mode: SQLite WAL Mode (High Concurrency)")
    print(f"  WSGI Engine:   Waitress Production Server ({threads} Worker Threads)")
    print("  Logging:       app.log & alerts.log (Rotating File Handler)")
    print("==========================================================")
    
    start_application()
    
    try:
        serve(app, host=host, port=port, threads=threads)
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Production server crash: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1)
