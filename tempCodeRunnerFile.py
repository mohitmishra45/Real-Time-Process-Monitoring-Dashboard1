import sys
import psutil
import platform
from datetime import datetime
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                           QTableWidget, QTableWidgetItem, QHeaderView, 
                           QMessageBox, QFrame, QComboBox)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor, QFont
import pyqtgraph as pg
import numpy as np
from collections import deque
import time

class ModernProcessMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Process Monitoring System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Theme state
        self.is_dark_theme = True
        
        # Initialize data structures
        self.cpu_data = deque(maxlen=100)
        self.memory_data = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        self.last_update = 0
        self.update_interval = 2000
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Top bar with title, theme toggle and search
        top_bar = QHBoxLayout()
        title = QLabel("Process Monitoring System")
        title.setObjectName("title")
        top_bar.addWidget(title)
        
        top_bar.addStretch()
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("🔍 Search Processes...")
        search_box.setFixedWidth(300)
        search_box.textChanged.connect(self.filter_processes)
        search_box.setObjectName("searchBox")
        top_bar.addWidget(search_box)
        
        # Add theme toggle button next to search
        self.theme_button = QPushButton("🌙")  # Moon emoji for dark mode
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setFixedSize(32, 32)  # Reduced from 40x40 to 32x32
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.clicked.connect(self.toggle_theme)
        top_bar.addWidget(self.theme_button)
        
        layout.addLayout(top_bar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left side - Monitoring panels
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)
        
        # Monitoring section with fixed height
        monitoring_layout = QHBoxLayout()
        monitoring_widget = QWidget()
        monitoring_widget.setLayout(monitoring_layout)
        monitoring_widget.setFixedHeight(250)  # Reduced height
        
        # CPU Usage panel
        cpu_panel = QFrame()
        cpu_layout = QVBoxLayout(cpu_panel)
        cpu_layout.setContentsMargins(15, 15, 15, 15)
        cpu_title = QLabel("CPU Usage")
        cpu_title.setStyleSheet("font-size: 18px; color: #7aa2f7; font-weight: bold;")
        cpu_layout.addWidget(cpu_title)
        
        self.cpu_plot = pg.PlotWidget()
        self.cpu_plot.setBackground('#24283b')
        self.cpu_plot.showGrid(x=True, y=True, alpha=0.2)
        self.cpu_plot.setYRange(0, 100)
        self.cpu_plot.setLabel('left', 'Usage %', color='#a9b1d6')
        self.cpu_plot.setFixedHeight(150)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color='#7aa2f7', width=2))
        cpu_layout.addWidget(self.cpu_plot)
        
        self.cpu_label = QLabel("Current: 0% | Freq: 0 MHz")
        self.cpu_label.setStyleSheet("font-size: 13px; color: #a9b1d6; padding: 5px;")
        cpu_layout.addWidget(self.cpu_label)
        monitoring_layout.addWidget(cpu_panel)
        
        # Memory Usage panel
        memory_panel = QFrame()
        memory_layout = QVBoxLayout(memory_panel)
        memory_layout.setContentsMargins(15, 15, 15, 15)
        memory_title = QLabel("Memory Usage")
        memory_title.setStyleSheet("font-size: 18px; color: #7aa2f7; font-weight: bold;")
        memory_layout.addWidget(memory_title)
        
        self.memory_plot = pg.PlotWidget()
        self.memory_plot.setBackground('#24283b')
        self.memory_plot.showGrid(x=True, y=True, alpha=0.2)
        self.memory_plot.setYRange(0, 100)
        self.memory_plot.setLabel('left', 'Usage %', color='#a9b1d6')
        self.memory_plot.setFixedHeight(150)
        self.memory_curve = self.memory_plot.plot(pen=pg.mkPen(color='#f7768e', width=2))
        memory_layout.addWidget(self.memory_plot)
        
        self.memory_label = QLabel("Used: 0 MB | Total: 0 MB | 0%")
        self.memory_label.setStyleSheet("font-size: 13px; color: #a9b1d6; padding: 5px;")
        memory_layout.addWidget(self.memory_label)
        monitoring_layout.addWidget(memory_panel)
        
        left_layout.addWidget(monitoring_widget)
        
        # Process list
        list_panel = QFrame()
        list_layout = QVBoxLayout(list_panel)
        list_layout.setContentsMargins(15, 15, 15, 15)
        list_title = QLabel("Running Processes")
        list_title.setStyleSheet("font-size: 18px; color: #7aa2f7; font-weight: bold;")
        list_layout.addWidget(list_title)
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(7)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "User", "CPU %", "Memory %", "Priority", "Actions"
        ])
        
        # Configure table appearance
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.verticalHeader().setVisible(False)
        self.process_table.setShowGrid(False)
        self.process_table.setAlternatingRowColors(True)
        
        # Set column widths
        column_widths = [100, 250, 200, 120, 120, 120, 140]  # Increased widths
        for i, width in enumerate(column_widths):
            self.process_table.setColumnWidth(i, width)
        
        list_layout.addWidget(self.process_table)
        left_layout.addWidget(list_panel)
        
        content_layout.addWidget(left_panel, stretch=7)
        
        # Right side - System Information
        self.right_panel = QFrame()
        self.right_panel.setMaximumWidth(300)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        info_title = QLabel("System Information")
        info_title.setObjectName("systemInfoTitle")
        right_layout.addWidget(info_title)
        
        self.system_info = self.get_system_info()
        for key, value in self.system_info.items():
            info_frame = QFrame()
            info_frame.setObjectName("infoFrame")
            info_layout = QVBoxLayout(info_frame)
            key_label = QLabel(key)
            key_label.setObjectName("infoKey")
            value_label = QLabel(value)
            value_label.setObjectName("infoValue")
            info_layout.addWidget(key_label)
            info_layout.addWidget(value_label)
            right_layout.addWidget(info_frame)
        
        right_layout.addStretch()
        content_layout.addWidget(self.right_panel, stretch=2)
        
        layout.addLayout(content_layout)
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)
        
        self.update_data()
        
        # Apply initial theme
        self.apply_theme()
        
    def get_system_info(self):
        info = {
            "OS": f"{platform.system()} {platform.version()}",
            "Processor": platform.processor(),
            "Cores": f"{psutil.cpu_count()} | Threads: {psutil.cpu_count(logical=True)}",
            "Memory": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        }
        return info
    
    def update_data(self):
        try:
            current_time = time.time()
            if current_time - self.last_update < self.update_interval / 1000:
                return
            self.last_update = current_time

            # Update CPU data
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_freq = psutil.cpu_freq()
            self.cpu_data.append(cpu_percent)
            self.cpu_label.setText(f"Current: {cpu_percent}% | Freq: {cpu_freq.current:.0f} MHz")
            
            # Update Memory data
            memory = psutil.virtual_memory()
            self.memory_data.append(memory.percent)
            used_gb = memory.used / (1024**3)
            total_gb = memory.total / (1024**3)
            self.memory_label.setText(f"Used: {used_gb:.1f} GB | Total: {total_gb:.1f} GB | {memory.percent}%")
            
            # Update graphs
            self.timestamps.append(len(self.cpu_data))
            
            # Update graph colors based on theme
            cpu_color = '#7aa2f7' if self.is_dark_theme else '#2c3e50'
            memory_color = '#f7768e' if self.is_dark_theme else '#dc3545'
            background_color = '#24283b' if self.is_dark_theme else '#ffffff'
            grid_color = '#414868' if self.is_dark_theme else '#e1e4e8'
            text_color = '#a9b1d6' if self.is_dark_theme else '#2c3e50'
            
            # Update CPU plot
            self.cpu_plot.setBackground(background_color)
            self.cpu_plot.getAxis('left').setPen(text_color)
            self.cpu_plot.getAxis('bottom').setPen(text_color)
            self.cpu_curve.setPen(pg.mkPen(color=cpu_color, width=2))
            
            # Update Memory plot
            self.memory_plot.setBackground(background_color)
            self.memory_plot.getAxis('left').setPen(text_color)
            self.memory_plot.getAxis('bottom').setPen(text_color)
            self.memory_curve.setPen(pg.mkPen(color=memory_color, width=2))
            
            self.cpu_curve.setData(list(self.timestamps), list(self.cpu_data))
            self.memory_curve.setData(list(self.timestamps), list(self.memory_data))
            
            # Update process table
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    pinfo = proc.info
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            processes = processes[:50]  # Limit to top 50 processes
            
            # Update table in batches
            self.process_table.setUpdatesEnabled(False)
            self.process_table.setRowCount(len(processes))
            
            # Set row height for all rows
            self.process_table.verticalHeader().setDefaultSectionSize(65)
            
            for i, proc in enumerate(processes):
                # Create items only once
                items = [
                    QTableWidgetItem(str(proc['pid'])),
                    QTableWidgetItem(proc['name']),
                    QTableWidgetItem(proc['username']),
                    QTableWidgetItem(f"{proc['cpu_percent']:.1f}%"),
                    QTableWidgetItem(f"{proc.get('memory_percent', 0):.1f}%"),
                    QTableWidgetItem("Low")
                ]
                
                # Set items in batch
                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.process_table.setItem(i, col, item)
                
                # Create and style the terminate button
                button_container = QWidget()
                button_container.setProperty("buttonContainer", True)
                button_layout = QHBoxLayout(button_container)
                button_layout.setContentsMargins(4, 4, 4, 4)
                button_layout.setSpacing(0)
                button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                kill_button = QPushButton("KILL")
                kill_button.setProperty("warning", True)
                kill_button.setFixedSize(70, 28)  # Reduced size
                kill_button.setCursor(Qt.CursorShape.PointingHandCursor)
                kill_button.clicked.connect(lambda checked, pid=proc['pid']: self.kill_process(pid))
                
                button_layout.addWidget(kill_button)
                self.process_table.setCellWidget(i, 6, button_container)
            
            self.process_table.setUpdatesEnabled(True)
                
        except Exception as e:
            print(f"Error updating data: {str(e)}")
    
    def kill_process(self, pid):
        try:
            process = psutil.Process(pid)
            
            # Check if it's a system process
            if process.username() in ['SYSTEM', 'LOCAL SERVICE', 'NETWORK SERVICE'] or pid <= 4:
                msg = QMessageBox(self)
                msg.setWindowTitle("System Process")
                msg.setText("Cannot terminate system process")
                msg.setInformativeText("This action could destabilize the system.")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.setDefaultButton(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # Ask for confirmation
            confirm_msg = QMessageBox(self)
            confirm_msg.setWindowTitle("Confirm Process Termination")
            confirm_msg.setText(f"Terminate Process: {process.name()}")
            confirm_msg.setInformativeText(f"PID: {pid}\nAre you sure you want to terminate this process?")
            confirm_msg.setIcon(QMessageBox.Icon.Question)
            confirm_msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            confirm_msg.setDefaultButton(QMessageBox.StandardButton.No)
            
            if confirm_msg.exec() == QMessageBox.StandardButton.Yes:
                process.terminate()
                try:
                    process.wait(timeout=3)
                    success_msg = QMessageBox(self)
                    success_msg.setWindowTitle("Success")
                    success_msg.setText("Process Terminated")
                    success_msg.setInformativeText(
                        f"Process {process.name()} (PID: {pid}) was terminated successfully."
                    )
                    success_msg.setIcon(QMessageBox.Icon.Information)
                    success_msg.exec()
                except psutil.TimeoutExpired:
                    force_msg = QMessageBox(self)
                    force_msg.setWindowTitle("Process Not Responding")
                    force_msg.setText(f"Process {process.name()} is not responding")
                    force_msg.setInformativeText("Do you want to force kill it?")
                    force_msg.setIcon(QMessageBox.Icon.Warning)
                    force_msg.setStandardButtons(
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if force_msg.exec() == QMessageBox.StandardButton.Yes:
                        process.kill()
                        QMessageBox.information(
                            self, "Success", 
                            f"Process {process.name()} (PID: {pid}) was force killed."
                        )
                    
        except psutil.AccessDenied:
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Access Denied")
            error_msg.setText("Administrative privileges required")
            error_msg.setInformativeText("You need administrator rights to terminate this process.")
            error_msg.setIcon(QMessageBox.Icon.Warning)
            error_msg.exec()
        except psutil.NoSuchProcess:
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Process Not Found")
            error_msg.setText("Process no longer exists")
            error_msg.setInformativeText("The process may have already been terminated.")
            error_msg.setIcon(QMessageBox.Icon.Warning)
            error_msg.exec()
        except Exception as e:
            error_msg = QMessageBox(self)
            error_msg.setWindowTitle("Error")
            error_msg.setText("Failed to terminate process")
            error_msg.setInformativeText(str(e))
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.exec()
        
        # Update the process list after kill attempt
        self.update_data()
    
    def filter_processes(self, text):
        for i in range(self.process_table.rowCount()):
            show = False
            for j in range(self.process_table.columnCount() - 1):  # Exclude the Actions column
                item = self.process_table.item(i, j)
                if item and text.lower() in item.text().lower():
                    show = True
                    break
            self.process_table.setRowHidden(i, not show)

    def apply_theme(self):
        # Dark theme styles
        dark_style = """
            QMainWindow {
                background-color: #1a1b26;
            }
            QLabel {
                color: #a9b1d6;
                font-size: 14px;
            }
            #title {
                font-size: 24px;
                color: #7aa2f7;
                font-weight: bold;
                padding: 10px;
                background-color: #24283b;
                border-radius: 8px;
            }
            #themeButton {
                background-color: #24283b;
                color: #a9b1d6;
                border: 2px solid #414868;
                border-radius: 20px;
                font-size: 16px;
            }
            #themeButton:hover {
                background-color: #2a2b36;
                border-color: #7aa2f7;
            }
            #searchBox {
                background-color: #24283b;
                color: #a9b1d6;
                border: 1px solid #414868;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
            }
            #searchBox:focus {
                border: 2px solid #7aa2f7;
            }
            QMessageBox {
                background-color: #1a1b26;
            }
            QMessageBox QLabel {
                color: #a9b1d6;
                font-size: 14px;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background-color: #7aa2f7;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #6a92e7;
            }
            QMessageBox QPushButton:pressed {
                background-color: #5a82d7;
            }
            QTableWidget {
                background-color: #24283b;
                color: #a9b1d6;
                border: none;
                gridline-color: #414868;
                selection-background-color: #364A82;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #1a1b26;
                color: #7aa2f7;
                border: none;
                border-right: 1px solid #414868;
                padding: 12px 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #2a2b36;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #414868;
            }
            QTableWidget::item:hover {
                background-color: #2a2b36;
            }
            QTableWidget::item:selected {
                background-color: #364A82;
                color: white;
            }
            QPushButton {
                background-color: #ff4757;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
                min-height: 30px;
                margin: 4px;
            }
            QPushButton:hover {
                background-color: #ff6b81;
                border: 2px solid #ffffff;
            }
            QPushButton:pressed {
                background-color: #ff4757;
            }
            QPushButton[warning="true"] {
                background-color: #ff4757;
                color: #ffffff !important;
                font-weight: 800;
                font-size: 13px;
                border: none;
                min-width: 70px;
                min-height: 28px;
                letter-spacing: 0.5px;
                text-align: center;
                padding: 2px 8px;
                text-transform: uppercase;
                border-radius: 4px;
            }
            QPushButton[warning="true"]:hover {
                background-color: #ff6b81;
                border: 1px solid #ffffff;
            }
            QPushButton[warning="true"]:pressed {
                background-color: #ff4757;
            }
            QFrame {
                background-color: #24283b;
                border-radius: 8px;
                border: 1px solid #414868;
            }
            QFrame:hover {
                border: 1px solid #7aa2f7;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #414868;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #7aa2f7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QWidget[buttonContainer="true"] {
                background-color: transparent;
                padding: 4px;
                margin: 2px;
            }
            #systemInfoTitle {
                font-size: 18px;
                color: #7aa2f7;
                font-weight: bold;
                margin-bottom: 10px;
            }
            #infoFrame {
                background-color: #2a2b36;
                border-radius: 4px;
                padding: 10px;
                margin: 5px 0;
                border: 1px solid #414868;
            }
            #infoKey {
                color: #7aa2f7;
                font-weight: bold;
                font-size: 14px;
            }
            #infoValue {
                color: #a9b1d6;
                font-size: 13px;
            }
        """

        # Light theme styles
        light_style = """
            QMainWindow {
                background-color: #f0f2f5;
            }
            QLabel {
                color: #2c3e50;
                font-size: 14px;
            }
            #title {
                font-size: 24px;
                color: #2c3e50;
                font-weight: bold;
                padding: 10px;
                background-color: white;
                border-radius: 8px;
            }
            #themeButton {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #e1e4e8;
                border-radius: 16px;
                font-size: 14px;
            }
            #themeButton:hover {
                background-color: #f6f8fa;
                border-color: #2c3e50;
            }
            #searchBox {
                background-color: white;
                color: #2c3e50;
                border: 1px solid #e1e4e8;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
            }
            #searchBox:focus {
                border: 2px solid #2c3e50;
            }
            QTableWidget {
                background-color: white;
                color: #2c3e50;
                border: none;
                gridline-color: #e1e4e8;
            }
            QHeaderView::section {
                background-color: #f6f8fa;
                color: #2c3e50;
                border: none;
                border-right: 1px solid #e1e4e8;
                padding: 12px 8px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e1e4e8;
            }
            QTableWidget::item:selected {
                background-color: #f1f8ff;
                color: #2c3e50;
            }
            QPushButton[warning="true"] {
                background-color: #dc3545;
                color: white !important;
                font-weight: 800;
                font-size: 13px;
                border: none;
                min-width: 70px;
                min-height: 28px;
            }
            QPushButton[warning="true"]:hover {
                background-color: #c82333;
                border: 2px solid #dc3545;
            }
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 14px;
                padding: 10px;
            }
            QMessageBox QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056b3;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e1e4e8;
            }
            QFrame:hover {
                border: 1px solid #2c3e50;
            }
            QScrollBar:vertical {
                border: none;
                background: #f6f8fa;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #c1c9d2;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a1aab4;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QWidget[buttonContainer="true"] {
                background-color: transparent;
                padding: 4px;
                margin: 2px;
            }
            #systemInfoTitle {
                font-size: 18px;
                color: #2c3e50;
                font-weight: bold;
                margin-bottom: 10px;
            }
            #infoFrame {
                background-color: white;
                border-radius: 4px;
                padding: 10px;
                margin: 5px 0;
                border: 1px solid #e1e4e8;
            }
            #infoKey {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
            }
            #infoValue {
                color: #2c3e50;
                font-size: 13px;
            }
        """

        self.setStyleSheet(dark_style if self.is_dark_theme else light_style)
        self.theme_button.setText("🌙" if self.is_dark_theme else "☀️")
        
        # Update the system info frames style
        for i in range(self.right_panel.layout().count() - 1):  # -1 to exclude the stretch
            widget = self.right_panel.layout().itemAt(i).widget()
            if isinstance(widget, QFrame):
                if self.is_dark_theme:
                    widget.setStyleSheet("""
                        QFrame {
                            background-color: #2a2b36;
                            border-radius: 4px;
                            padding: 10px;
                            margin: 5px 0;
                        }
                    """)
                else:
                    widget.setStyleSheet("""
                        QFrame {
                            background-color: white;
                            border-radius: 4px;
                            border: 1px solid #e1e4e8;
                            padding: 10px;
                            margin: 5px 0;
                        }
                    """)

        # Update graph colors
        if hasattr(self, 'cpu_plot'):
            background_color = '#24283b' if self.is_dark_theme else '#ffffff'
            text_color = '#a9b1d6' if self.is_dark_theme else '#2c3e50'
            grid_color = '#414868' if self.is_dark_theme else '#e1e4e8'
            
            self.cpu_plot.setBackground(background_color)
            self.memory_plot.setBackground(background_color)
            
            # Update axis colors
            for plot in [self.cpu_plot, self.memory_plot]:
                plot.getAxis('left').setPen(text_color)
                plot.getAxis('bottom').setPen(text_color)
                plot.getAxis('left').setTextPen(text_color)
                plot.getAxis('bottom').setTextPen(text_color)
                
                # Update grid
                plot.showGrid(x=True, y=True)
                plot.getAxis('left').setGrid(True)
                plot.getAxis('bottom').setGrid(True)
                
            # Update curve colors
            self.cpu_curve.setPen(pg.mkPen(color='#7aa2f7' if self.is_dark_theme else '#2c3e50', width=2))
            self.memory_curve.setPen(pg.mkPen(color='#f7768e' if self.is_dark_theme else '#dc3545', width=2))

        # Update monitoring panel titles and labels
        title_color = '#7aa2f7' if self.is_dark_theme else '#2c3e50'
        text_color = '#a9b1d6' if self.is_dark_theme else '#2c3e50'
        
        for widget in self.findChildren(QLabel):
            if 'title' in widget.objectName().lower():
                widget.setStyleSheet(f"font-size: 18px; color: {title_color}; font-weight: bold;")
            elif widget in [self.cpu_label, self.memory_label]:
                widget.setStyleSheet(f"font-size: 13px; color: {text_color}; padding: 5px;")

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

def main():
    app = QApplication(sys.argv)
    window = ModernProcessMonitor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 