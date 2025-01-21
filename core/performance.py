import time
import os
import json
import psutil
import logging
import random
from core.drive_check import get_removable_and_external_drives_details


# Configure logging
logging.basicConfig(filename='driveman.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_performance_tests(drives):
    """Run basic performance tests (read/write speed) on the provided drives."""
    results = {}
    for drive in drives:
        drive_letter = drive['drive_letter']  # Access drive letter from the dictionary
        try:
            print(f"Running performance tests on {drive_letter}...")
            results[drive_letter] = {
                "sequential": {
                    "write_speed": test_write_speed(drive_letter),
                    "read_speed": test_read_speed(drive_letter)
                },
                "random": {
                    "io_speed": test_random_io(drive_letter)
                },
                "file_operations": test_file_operations(drive_letter),
                "benchmark": run_benchmark(drive_letter)
            }
            
        except Exception as e:
            logging.error(f"Error running performance tests on {drive_letter}: {e}")
            results[drive_letter] = {"error": str(e)}

    return results

def test_write_speed(drive):
    """Test write speed of the given drive."""
    test_size_mb = 100 # Increased test size
    temp_file = os.path.join(drive, "temp_test_file.bin") # Use .bin for binary data
    try:
        start_time = time.perf_counter() # Use perf_counter for better precision
        with open(temp_file, 'wb') as f: # Write binary data
            f.write(os.urandom(test_size_mb * 1024 * 1024)) # Write random data
        write_speed = test_size_mb / (time.perf_counter() - start_time)  # MB/s
        return write_speed
    except Exception as e:
        logging.error(f"Error testing write speed on {drive}: {e}")
        return f"Error: {str(e)}"
    finally:
        try:
            os.remove(temp_file)
        except Exception as e:
            logging.error(f"Error removing temp file on {drive}: {e}")

def test_read_speed(drive):
    """Test read speed of the given drive."""
    test_size_mb = 100
    temp_file = os.path.join(drive, "temp_test_file.bin")
    try:
        with open(temp_file, 'wb') as f:
            f.write(os.urandom(test_size_mb * 1024 * 1024))
        start_time = time.perf_counter()
        with open(temp_file, 'rb') as f:
            f.read()
        read_speed = test_size_mb / (time.perf_counter() - start_time)
        return read_speed
    except Exception as e:
        logging.error(f"Error testing read speed on {drive}: {e}")
        return f"Error: {str(e)}"
    finally:
        try:
            os.remove(temp_file)
        except Exception as e:
            logging.error(f"Error removing temp file on {drive}: {e}")

def test_random_io(drive):
    """Test random read/write performance."""
    test_size_mb = 50
    block_size = 4096  # 4KB blocks
    temp_file = os.path.join(drive, "random_test.bin")
    
    try:
        # Create test file
        with open(temp_file, 'wb') as f:
            f.write(os.urandom(test_size_mb * 1024 * 1024))
        
        # Random read test
        start_time = time.perf_counter()
        with open(temp_file, 'rb') as f:
            for _ in range(1000):
                pos = random.randrange(0, test_size_mb * 1024 * 1024 - block_size)
                f.seek(pos)
                f.read(block_size)
        
        random_read_speed = test_size_mb / (time.perf_counter() - start_time)
        return random_read_speed
    finally:
        try:
            os.remove(temp_file)
        except Exception as e:
            logging.error(f"Error removing temp file: {e}")

def test_file_operations(drive):
    """Test small file operations performance."""
    test_dir = os.path.join(drive, "test_dir")
    num_files = 100
    results = {}
    
    try:
        # Test directory creation
        start_time = time.perf_counter()
        os.makedirs(test_dir, exist_ok=True)
        results['dir_creation'] = time.perf_counter() - start_time

        # Test small file creation
        start_time = time.perf_counter()
        for i in range(num_files):
            with open(os.path.join(test_dir, f"test_{i}.txt"), 'w') as f:
                f.write("test" * 100)
        results['file_creation'] = time.perf_counter() - start_time

        return results
    finally:
        try:
            import shutil
            shutil.rmtree(test_dir)
        except Exception as e:
            logging.error(f"Error cleaning up test directory: {e}")

def run_benchmark(drive):
    """Run more comprehensive benchmark using psutil."""
    try:
        disk_io_before = psutil.disk_io_counters(perdisk=True)[drive]
        time.sleep(1)  # Short delay to capture changes
        disk_io_after = psutil.disk_io_counters(perdisk=True)[drive]

        read_bytes = disk_io_after.read_bytes - disk_io_before.read_bytes
        write_bytes = disk_io_after.write_bytes - disk_io_before.write_bytes
        read_time = (disk_io_after.read_time - disk_io_before.read_time) / 1000 # convert ms to s
        write_time = (disk_io_after.write_time - disk_io_before.write_time) / 1000

        read_speed = (read_bytes / (1024 * 1024)) / read_time if read_time > 0 else 0
        write_speed = (write_bytes / (1024 * 1024)) / write_time if write_time > 0 else 0
        return {"read_speed": read_speed, "write_speed": write_speed}

    except KeyError:
        logging.error(f"Drive {drive} not found by psutil")
        return None
    except Exception as e:
        logging.error(f"Error running benchmark on {drive}: {e}")
        return None

def save_results(results, filename="benchmark_results.json"):
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=4)
        logging.info(f"Benchmark results saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving benchmark results: {e}")

if __name__ == "__main__":
    drives = get_removable_and_external_drives_details()
    if not drives:
        print("No removable drives found, running tests on local drives")
        drives = ['C:', 'D:']

    perf_results = run_performance_tests(drives)
    benchmark_results = {}
    for drive in drives:
        drive_letter = drive['drive_letter']  # Access drive letter from the dictionary
        benchmark_results[drive_letter] = run_benchmark(drive_letter)  # Use drive letter as key

    save_results({"performance_tests": perf_results, "benchmarks": benchmark_results})

    print("Performance Tests Results:")
    print(json.dumps(perf_results, indent=4))
    print("\nBenchmark Results:")
    print(json.dumps(benchmark_results, indent=4))

