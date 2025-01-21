import win32api
import win32file
import os
import wmi
import logging
import datetime
import json
import threading
import time
import subprocess
import psutil
import pythoncom
from wmi import x_wmi_invalid_query  # Add this import

# Configure logging
logging.basicConfig(
    filename='driveman.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def is_external_hdd(disk):
    """Enhanced external drive detection."""
    try:
        # Check multiple characteristics
        if any([
            disk.InterfaceType in ["USB", "1394", "eSATA"],
            "USB" in (disk.PNPDeviceID or ""),
            disk.MediaType == "External hard disk media",
            getattr(disk, 'RemovableMedia', False),
            getattr(disk, 'Portable', False)
        ]):
            return True
        
        # Additional USB detection
        if hasattr(disk, 'DeviceID'):
            try:
                controller = disk.associators("Win32_USBControllerDevice")
                if controller:
                    return True
            except:
                pass
                
    except Exception as e:
        logging.error(f"Error in external drive detection: {e}")
    return False

def get_wmi_drive_details(drive_letter, w):
    """Fetch detailed information about a drive using WMI."""
    try:
        for disk in w.Win32_DiskDrive():
            try:
                # Use associators() method for better performance
                for partition in disk.associators("Win32_DiskDriveToDiskPartition"):
                    for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                        if logical_disk.DeviceID == drive_letter:
                            details = {
                                "model": getattr(disk, 'Model', 'N/A'),
                                "interface_type": getattr(disk, 'InterfaceType', 'N/A'),
                                "serial_number": getattr(disk, 'SerialNumber', 'N/A'),
                                "media_type": getattr(disk, 'MediaType', 'N/A'),
                                "file_system": getattr(logical_disk, 'FileSystem', 'N/A'),
                                "drive_type_wmi": getattr(logical_disk, 'DriveType', 'N/A'),
                                "volume_serial": getattr(logical_disk, 'VolumeSerialNumber', 'N/A'),
                                "driver_version": getattr(disk, 'DriverVersion', 'N/A'),
                                "size_bytes": getattr(disk, 'Size', 0),
                                "status": getattr(disk, 'Status', 'Unknown'),
                            }
                            details["is_external"] = is_external_hdd(disk)
                            return details
            except x_wmi_invalid_query as e:
                logging.warning(f"WMI invalid query for partition: {e}")
            except Exception as e:
                logging.warning(f"Error processing disk {disk.DeviceID}: {e}")
    except Exception as e:
        logging.error(f"General WMI error: {e}")
    return {}

def get_win32_drive_details(drive):
    """Fetch drive details using win32api."""
    drive_info = {
        "volume_name": "N/A",
        "total_gb": "N/A",
        "free_gb": "N/A",
    }
    try:
        volume_info = win32api.GetVolumeInformation(drive)
        drive_info["volume_name"] = volume_info[0]
        
        free_bytes, total_bytes, _ = win32api.GetDiskFreeSpaceEx(drive)
        drive_info.update({
            "total_gb": total_bytes / (1024**3),
            "free_gb": free_bytes / (1024**3),
            "usage_history": [{
                "timestamp": datetime.datetime.now().isoformat(),
                "free_gb": free_bytes / (1024**3)
            }]
        })
    except win32api.error as e:
        logging.warning(f"Win32API details unavailable for {drive}: {e}")
    return drive_info

def get_win32file_drive_details(drive):
    """Fetch drive details using win32file."""
    drive_info = {
        "total_gb": "N/A",
        "free_gb": "N/A",
    }
    try:
        drive_type = win32file.GetDriveType(drive)
        if drive_type == win32file.DRIVE_FIXED or drive_type == win32file.DRIVE_REMOVABLE:
            free_bytes, total_bytes, _ = win32api.GetDiskFreeSpaceEx(drive)
            drive_info.update({
                "total_gb": total_bytes / (1024**3),
                "free_gb": free_bytes / (1024**3),
            })
    except Exception as e:
        logging.warning(f"Error fetching details using win32file for {drive}: {e}")
    return drive_info

def get_subprocess_drive_details(drive):
    """Fetch drive details using subprocess (using 'wmic' command)."""
    drive_info = {}
    try:
        result = subprocess.run(['wmic', 'logicaldisk', 'where', f"DeviceID='{drive}'", 'get', 'FileSystem,DriveType,VolumeSerialNumber'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            output = result.stdout.strip().split('\n')
            drive_info['file_system'] = output[1].split()[0]
            drive_info['drive_type'] = output[1].split()[1]
    except Exception as e:
        logging.warning(f"Error fetching details using subprocess for {drive}: {e}")
    return drive_info

def get_psutil_drive_details(drive):
    """Fetch drive details using psutil."""
    drive_info = {}
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            if partition.device == drive:
                usage = psutil.disk_usage(partition.mountpoint)
                drive_info['total_gb'] = usage.total / (1024**3)
                drive_info['free_gb'] = usage.free / (1024**3)
                drive_info['file_system'] = partition.fstype
    except Exception as e:
        logging.warning(f"Error fetching details using psutil for {drive}: {e}")
    return drive_info

def combine_drive_details(drive_letter, w):
    """Consolidate drive details from all available methods."""
    details = {
        "drive_letter": drive_letter,
        "volume_name": "N/A",
        "total_gb": "N/A",
        "free_gb": "N/A",
        "file_system": "N/A",
        "drive_type_wmi": "N/A",
        "volume_serial": "N/A",
        "model": "N/A",
        "interface_type": "N/A",
        "serial_number": "N/A",
        "media_type": "N/A",
        "usage_history": [],
        "is_external": False
    }
    
    # WMI details
    details.update(get_wmi_drive_details(drive_letter, w))
    
    # Fallback to win32api if WMI details are not found
    if not details["model"]:
        details.update(get_win32_drive_details(drive_letter))
    
    # Fallback to win32file if both WMI and win32api details are not found
    if not details["model"]:
        details.update(get_win32file_drive_details(drive_letter))
    
    # Fallback to subprocess if no details yet
    if not details["model"]:
        details.update(get_subprocess_drive_details(drive_letter))
    
    # Fallback to psutil if still no details found
    if not details["model"]:
        details.update(get_psutil_drive_details(drive_letter))
    
    return details

def get_removable_and_external_drives_details():
    """Detects removable and external drives and consolidates details."""
    drives_info = []
    drive_strings = win32api.GetLogicalDriveStrings()
    
    # Ensure COM is initialized before using WMI
    pythoncom.CoInitialize()  # Initialize COM for this thread
    w = wmi.WMI()

    logging.info("Starting drive detection...")
    for drive in drive_strings.split('\x00'):
        if drive and os.path.isdir(drive):
            try:
                drive_details = combine_drive_details(drive, w)

                # Additional check for external HDDs
                if drive_details.get("is_external"):
                    drives_info.append(drive_details)
                    logging.info(f"Detected drive: {drive_details}")
            except Exception as e:
                logging.error(f"Error processing drive {drive}: {e}")
        else:
            logging.debug(f"Skipped invalid or non-existent drive: {drive}")

    logging.info("Drive detection completed.")
    return drives_info

def save_drive_data(data, filename=None):
    """Saves drive data to a JSON file."""
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"drive_data_{timestamp}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Drive data saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving drive data: {e}")

def monitor_drive_changes():
    """Monitors the system for new drive connections and disconnections."""
    previous_drives = set(win32api.GetLogicalDriveStrings().split('\x00'))

    while True:
        try:
            current_drives = set(win32api.GetLogicalDriveStrings().split('\x00'))

            # Detect newly connected drives
            new_drives = current_drives - previous_drives
            if new_drives:
                logging.info(f"New drives connected: {new_drives}")
                drives_info = get_removable_and_external_drives_details()
                for drive in drives_info:
                    if drive["drive_letter"] in new_drives:
                        print(json.dumps(drive, indent=4))

            # Detect disconnected drives
            removed_drives = previous_drives - current_drives
            if removed_drives:
                logging.info(f"Drives disconnected: {removed_drives}")

            previous_drives = current_drives
            time.sleep(10)  # Check every 5 seconds
        except KeyboardInterrupt:
            logging.info("Drive monitoring stopped.")
            break
        except Exception as e:
            logging.error(f"Error monitoring drives: {e}")

if __name__ == "__main__":
    threading.Thread(target=monitor_drive_changes, daemon=True).start()
    print("Monitoring for drive changes. Press Ctrl+C to stop.")

    while True:
        try:
            time.sleep(1)  # Keep the main thread alive
        except KeyboardInterrupt:
            print("Exiting...")
            break
