from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QLabel, QScrollArea, QTableWidget, \
    QTableWidgetItem, QPushButton, QGridLayout,QStatusBar
from PyQt5.QtGui import QColor, QBrush, QPainter
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from core.drive_check import get_removable_and_external_drives_details
from PyQt5.QtCore import Qt

from core.performance import run_performance_tests
from core.health import check_drive_health
from utils.logger import log_info

class DriveManDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DriveMan - Dashboard")
        self.setGeometry(100, 100, 389, 580)
        # ... in DriveManDashboard class ...
        self.setStyleSheet(open('E:\\vsc\\driveman\\resources\\styles\\dashboard.scss').read())

        # Add a status bar for feedback
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Main layout
        main_layout = QVBoxLayout()

        

        # Drive listing
        main_layout.addWidget(self.create_drive_list_panel())

        # Performance metrics
        main_layout.addWidget(self.create_performance_metrics_table())

        # Health visualization
        main_layout.addWidget(self.create_health_visualization())

        # Action buttons
        main_layout.addWidget(self.create_action_buttons())

        # Set central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def load_initial_data(self):
        """Load data after UI initialization."""
        self.status_bar.showMessage("Loading drive details...")

        try:
            # Perform heavy operations like fetching drive details
            drives = get_removable_and_external_drives_details()
            self.populate_drive_list(drives)
            self.status_bar.showMessage("Drive details loaded.", 5000)
        except Exception as e:
            self.status_bar.showMessage("Error loading data.", 5000)
            log_info(f"Error in load_initial_data: {e}")

    def populate_drive_list(self, drives):
        """Populate drive list panel with the fetched details."""
        # Update UI with drive information
        # Placeholder for actual implementation
        pass


    def create_drive_list_panel(self):
        """Create the drive listing panel with actual drive data."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout()

        label = QLabel("Connected Drives")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)

        drives = get_removable_and_external_drives_details()

        if drives:
            # Bar Graph Visualization
            bar_series = QBarSeries()
            categories = []

            for drive in drives:
                bar_set = QBarSet(drive["drive_letter"])
                bar_set.append(drive["total_gb"])
                bar_series.append(bar_set)
                categories.append(drive["drive_letter"])

            # Create chart
            chart = QChart()
            chart.addSeries(bar_series)
            chart.setTitle("Storage Capacity of Connected Drives")
            chart.setAnimationOptions(QChart.SeriesAnimations)

            # Axis configuration
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            chart.addAxis(axis_x, Qt.AlignBottom)
            bar_series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setTitleText("Storage Capacity (GB)")
            chart.addAxis(axis_y, Qt.AlignLeft)
            bar_series.attachAxis(axis_y)

            # Chart view
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            layout.addWidget(chart_view)
        else:
            # Show a message when no devices are found
            no_device_label = QLabel("No device found. Please connect a device.")
            no_device_label.setStyleSheet("font-size: 14px; color: red; padding: 10px;")
            layout.addWidget(no_device_label)

        frame.setLayout(layout)
        return frame




    def create_performance_metrics_table(self):
        """Create the performance metrics table with actual performance data."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout()

        label = QLabel("Performance Metrics")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)

        table = QTableWidget(8, 3)  # Increased rows to accommodate more metrics
        table.setHorizontalHeaderLabels(["Metric", "Read", "Write"])
        table.setColumnWidth(0, 70)
        table.setColumnWidth(1, 70)
        table.setColumnWidth(2, 70)

        # Fetch actual drive details and pass them to the performance testing function
        drives = get_removable_and_external_drives_details()  # Get the actual drives
        performance_data = run_performance_tests(drives)  # Pass the drives to run performance tests

        for row, data in enumerate(performance_data):
            metric = data[0] if len(data) > 0 else "Unknown"
            read = data[1] if len(data) > 1 else "N/A"
            write = data[2] if len(data) > 2 else "N/A"

            read_item = QTableWidgetItem(str(read))
            write_item = QTableWidgetItem(str(write))

            # Set background color based on performance thresholds (optional)
            # ... (your existing color-coding logic) ...

            table.setItem(row, 0, QTableWidgetItem(metric))
            table.setItem(row, 1, read_item)
            table.setItem(row, 2, write_item)

        layout.addWidget(table)
        frame.setLayout(layout)
        return frame



    def create_health_visualization(self):
        """Create the health visualization grid with actual sector health data."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout()

        label = QLabel("Drive Sector Health Visualization")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)

        # Grid visualization
        grid = QGridLayout()
        grid.setSpacing(5)

        # Fetch actual health data (assuming health_data gives a list of health statuses per sector)
        health_data = [check_drive_health(drive['drive_letter']) for drive in get_removable_and_external_drives_details()]

        # Calculate rows and columns dynamically based on the number of sectors you want to display
        # Adjust this depending on the total number of sectors per drive and how many you want to visualize
        total_sectors = len(health_data)
        rows = (total_sectors // 10) + (1 if total_sectors % 10 else 0)  # 10 sectors per row
        cols = 10  # Fixed number of columns (can be adjusted)

        # Populate the grid with sector health data
        for row in range(rows):
            for col in range(cols):
                sector_index = row * cols + col
                if sector_index < total_sectors:
                    value = health_data[sector_index]
                    color = (
                        "green" if value == "Healthy" else
                        "red" if value == "Unhealthy" else
                        "orange" if value == "Warning" else
                        "gray"
                    )
                    cell = QLabel()
                    cell.setFixedSize(30, 30)  # Smaller cells for sector representation
                    cell.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
                    grid.addWidget(cell, row, col)

        layout.addLayout(grid)
        frame.setLayout(layout)
        return frame


    def create_action_buttons(self):
        """Create action buttons with proper event handling."""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QHBoxLayout()

        benchmark_button = QPushButton("Run Benchmark")
        health_check_button = QPushButton("Check Health")
        export_button = QPushButton("Export Report")

        # You can add signals here for actions like clicking the buttons
        benchmark_button.clicked.connect(self.run_benchmark)
        health_check_button.clicked.connect(self.check_health)
        export_button.clicked.connect(self.export_report)

        layout.addWidget(benchmark_button)
        layout.addWidget(health_check_button)
        layout.addWidget(export_button)

        frame.setLayout(layout)
        return frame



    def run_benchmark(self):
        """Action for running the benchmark."""
        try:
            drives = get_removable_and_external_drives_details() 
            performance_results = run_performance_tests(drives) 

            # Update the performance metrics table (assuming you have a method for this)
            self.update_performance_metrics_table(performance_results) 

            # Optionally, update the status bar with a success message
            self.status_bar.showMessage("Benchmark completed successfully.", 5000) 

        except Exception as e:
            # Handle potential errors during benchmarking
            self.status_bar.showMessage(f"Benchmark failed: {str(e)}", 5000)
            print(f"Benchmark failed: {e}") 
            # Log the error 
            log_info(f"Benchmark failed: {e}")


    def update_performance_metrics_table(self, performance_data):
        """Updates the performance metrics table with the given data."""
        table = self.findChild(QTableWidget)  # Assuming the table has a name or you can find it by hierarchy
        if table is not None:
            # Clear existing data
            table.setRowCount(0)

            # Update table content with new data
            for row, data in enumerate(performance_data):
                # Unpack the data safely, with default values if missing
                metric = data[0] if len(data) > 0 else "Unknown"
                read = data[1] if len(data) > 1 else "N/A"
                write = data[2] if len(data) > 2 else "N/A"

                read_item = QTableWidgetItem(str(read))
                write_item = QTableWidgetItem(str(write))

                # Set background color based on performance thresholds (optional)
                # ... (similar logic as in create_performance_metrics_table)

                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(metric))
                table.setItem(row, 1, read_item)
                table.setItem(row, 2, write_item)
        else:
            print("Error: Performance metrics table not found.")
            

    def check_health(self):
        """Action for checking the health of drives."""
        try:
            drives = get_removable_and_external_drives_details()
            health_results = {}

            for drive in drives:
                drive_letter = drive['drive_letter']
                health_status = check_drive_health(drive_letter)
                health_results[drive_letter] = health_status

            # Update the health visualization in the UI
            self.update_health_visualization(health_results) 

            # Optionally, update the status bar with a success message
            self.status_bar.showMessage("Health check completed successfully.", 5000) 

        except Exception as e:
            # Handle potential errors during health checks
            self.status_bar.showMessage(f"Health check failed: {str(e)}", 5000)
            print(f"Health check failed: {e}") 
            # Log the error 
            log_info(f"Health check failed: {e}") 

    def update_health_visualization(self, health_results):
        """Updates the health visualization grid with the given health data."""
        # ... (Your existing grid population logic from create_health_visualization) ...

    def export_report(self):
        """Action for exporting the report."""
        print("Exporting Report...")
