import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.dashboard import Dashboard
from core.drive_check import get_removable_drives_details
from core.performance import run_performance_tests  # Assuming performance testing function
from core.health import check_health  # Assuming health check function
from utils.logger import setup_logger
from utils.config import load_config  # Assuming configuration loading function

# Add paths for each directory to sys.path dynamically based on the current file's directory
base_path = os.path.dirname(os.path.abspath("E:\\vsc\\driveman"))  # Get the current directory

sys.path.append(os.path.join(base_path, 'ui'))  # UI directory
sys.path.append(os.path.join(base_path, 'core'))  # Core directory
sys.path.append(os.path.join(base_path, 'utils'))  # Utils directory
sys.path.append(os.path.join(base_path, 'resources'))  # Resources directory

print(f"sys.path: {sys.path}")