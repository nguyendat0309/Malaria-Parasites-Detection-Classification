"""
Blood Cell Analysis Application
Main entry point for the GUI application.

Usage:
    python main.py
    
Or double-click: run_app.bat
"""

import sys
import os

# Ensure the application directory is in path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)


def main():
    """Launch the Blood Cell Analysis application."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont, QIcon
    from PyQt6.QtCore import Qt
    
    from gui.main_window import MainWindow
    
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    
    # Application info
    app.setApplicationName("Blood Cell Analysis")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Malaria Detection Project")
    
    # Set style
    app.setStyle("Fusion")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
