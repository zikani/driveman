# core/health.py

import logging
import wmi
import win32api
import win32file
from subprocess import run, PIPE
import os
import psutil
import winreg
from ctypes import *
from datetime import datetime

def check_drive_health(drive_letter):
    """Comprehensive drive health check."""
    health_status = {
        "status": "Unknown",
        "smart_status": "Unknown",
        "temperature": None,
        "fragmentation": None,
        "space_usage": None,
        "errors": [],
        "warnings": [],
        "last_check": datetime.now().isoformat()
    }
    
    try:
        # Basic drive checks
        if not win32file.GetDriveType(drive_letter):
            health_status["errors"].append("Drive not accessible")
            return health_status

        # Space usage
        usage = psutil.disk_usage(drive_letter)
        health_status["space_usage"] = {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent
        }

        # SMART status
        health_status["smart_attributes"] = get_smart_attributes(drive_letter)
        
        # Temperature
        health_status["temperature"] = check_disk_temperature(drive_letter)
        
        # Fragmentation
        health_status["fragmentation"] = check_fragmentation(drive_letter)

        # Overall status assessment
        if not health_status["errors"]:
            if usage.percent > 90:
                health_status["warnings"].append("Low disk space")
            if health_status["temperature"] and health_status["temperature"] > 50:
                health_status["warnings"].append("High temperature")
            
            health_status["status"] = "Warning" if health_status["warnings"] else "Healthy"

    except Exception as e:
        health_status["errors"].append(f"Health check error: {str(e)}")
        health_status["status"] = "Error"

    return health_status

def monitor_drive_health(drive_letter, interval_minutes=60):
    """Monitor drive health periodically."""
    # Implementation for periodic health monitoring
    pass

def get_smart_attributes(drive_letter):
    """Get SMART attributes for the drive."""
    try:
        # Using PowerShell to get SMART data
        cmd = f"Get-WmiObject -Namespace root\\wmi -Class MSStorageDriver_ATAPISmartData | Select-Object VendorSpecific"
        result = run(['powershell', '-Command', cmd], capture_output=True, text=True)
        
        if result.returncode == 0:
            return parse_smart_data(result.stdout)
        return None
    except Exception as e:
        logging.error(f"Error getting SMART attributes: {e}")
        return None

def check_disk_temperature(drive_letter):
    """Check disk temperature using SMART data."""
    try:
        cmd = f"wmic /namespace:\\\\root\\wmi path MSAcpi_ThermalZoneTemperature get CurrentTemperature"
        result = run(cmd.split(), capture_output=True, text=True)
        if result.returncode == 0:
            temp = float(result.stdout.split('\n')[1])
            return (temp / 10.0) - 273.15  # Convert to Celsius
        return None
    except Exception as e:
        logging.error(f"Error checking disk temperature: {e}")
        return None

def parse_smart_data(smart_data):
    """Parse SMART data from the output."""
    # Implement the parsing logic here
    parsed_data = {}
    # Example parsing logic (to be replaced with actual logic)
    lines = smart_data.splitlines()
    for line in lines:
        if "VendorSpecific" in line:
            parsed_data["VendorSpecific"] = line.split(":")[1].strip()
    return parsed_data

def parse_defrag_output(output):
    """Parse defrag command output to extract fragmentation percentage."""
    try:
        # Simple parsing logic - adjust based on actual output format
        for line in output.splitlines():
            if "%" in line:
                return int(''.join(filter(str.isdigit, line)))
        return None
    except Exception as e:
        logging.error(f"Error parsing defrag output: {e}")
        return None

def check_fragmentation(drive_letter):
    """Check drive fragmentation level."""
    try:
        cmd = f"defrag {drive_letter} /A"
        result = run(cmd.split(), capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output to get fragmentation percentage
            return parse_defrag_output(result.stdout)
        return None
    except Exception as e:
        logging.error(f"Error checking fragmentation: {e}")
        return None
