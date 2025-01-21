import sys
import os
from utils.path_utils import ensure_dir
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from ui.dashboard import DriveManDashboard
from utils.logger import log_info
from utils.config import setup_logger

# Ensure base directories exist
ensure_dir(os.path.join(os.path.dirname(__file__), 'logs'))

# Add paths dynamically based on the current file's directory
base_path = os.path.dirname(os.path.abspath("E:\vsc\driveman"))
paths = ['ui', 'core', 'utils', 'resources']
for path in paths:
    full_path = os.path.join(base_path, path)
    if full_path not in sys.path:
        sys.path.append(full_path)

def main():
    try:
        # Initialize logging
        setup_logger()
        log_info("Application started")

        # Initialize PyQt application
        app = QApplication(sys.argv)
        dashboard = DriveManDashboard()

        # Delay heavy operations until after UI is displayed
        QTimer.singleShot(0, dashboard.load_initial_data)

        dashboard.show()
        sys.exit(app.exec_())
    except Exception as e:
        log_info(f"Error initializing application: {e}")
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
