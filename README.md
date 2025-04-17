# Real-Time-Process-Monitoring-System

## Overview
This is a comprehensive Python application for system process monitoring using PyQt6 and pyqtgraph. It features a modern, customizable interface that provides real-time insights into CPU and memory usage, running processes, and system information.

## Features
- **Real-time Monitoring:** Tracks CPU and memory usage dynamically with live graphs and detailed system metrics.
- **Intuitive UI:** A modern, responsive interface built with PyQt6, supporting both dark and light themes.
- **Process Management:** Allows users to search, filter, and safely terminate processes with confirmation dialogs.
- **System Information:** Displays OS details, processor information, core count, and total memory.
- **Efficient Data Handling:** Utilizes `QTimer` and `psutil` for optimized data collection and updates.
- **Error Handling:** Robust exception handling for smooth user experience.

## Installation
### Prerequisites
Ensure you have Python installed (>=3.8). Then, install the required dependencies:
```sh
pip install PyQt6 pyqtgraph psutil
```

## Usage
Run the application using:
```sh
python main.py
```

## Screenshots
![image](https://github.com/user-attachments/assets/fe643c04-15f8-4671-b624-bb7aa0f03052)
![image](https://github.com/user-attachments/assets/06316011-8791-4ef5-9246-4751f0eb74a8)


## Future Enhancements
- Add network usage monitoring
- Implement process resource consumption tracking
- Introduce system notification alerts

## Related Questions
- How does the application handle different process termination scenarios?
- What performance optimizations are implemented in the real-time monitoring system?
- How can the application be extended to support more advanced system monitoring features?

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors
- Kartik Singh Senger
- Mohit Kumar Mishra
