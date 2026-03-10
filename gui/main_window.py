"""
Main Window for the Blood Cell Analysis application.
"""

import os
import shutil
from statistics import median
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QMessageBox, QComboBox, 
                              QLabel, QFileDialog, QDialog, QFormLayout,
                              QFrame, QSplitter, QProgressDialog, QApplication, QGridLayout,QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor
from PyQt6.QtWidgets import QScrollArea
from gui.image_viewer import ImageViewer
from gui.widgets import ThumbnailBar, ResultPanel, StyledButton
from core.pipeline import AnalysisPipeline
from core.config import cfg


class PredictionWorker(QThread):
    """Background worker for running predictions."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, pipeline, image_path):
        super().__init__()
        self.pipeline = pipeline
        self.image_path = image_path
    
    def run(self):
        try:
            results = self.pipeline.predict_image(self.image_path)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blood Cell Analysis - Malaria Detection")
        self._apply_initial_geometry()
        
        # Dark theme palette
        self.setup_theme()
        
        self.pipeline = None
        self.current_image_path = None
        self.predictions = {}
        self.worker = None
        
        self.setup_ui()
        self.load_input_images()
        
        # Delayed pipeline initialization
        QTimer.singleShot(100, self.initialize_pipeline)

    def _apply_initial_geometry(self):
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry()  # <-- đã trừ taskbar

        target = QSize(1400, 900)
        w = min(target.width(), int(avail.width() * 0.96))
        h = min(target.height(), int(avail.height() * 0.96))

        self.resize(w, h)
        self.move(avail.center() - self.rect().center())


    def setup_theme(self):
        """Set up the application color theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a2a3a, stop:0.5 #1e3a4a, stop:1 #1a2a3a);
            }
            QMessageBox {
                background-color: #2a3a4a;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #3a5a7a;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
            }
        """)

    def setup_ui(self):
        """Build the user interface."""
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # --- TOP TOOLBAR ---
        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)
        
        # --- MAIN CONTENT (Fixed 3 regions) ---
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(0)

        # ===== (1) LEFT TOP: viewer + action bar =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Action bar (Predict/Delete/Reset/Mode)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(15)

        self.btn_predict = StyledButton("Predict", "#4caf50", "#66bb6a", "#388e3c")
        self.btn_predict.setFixedWidth(160)
        self.btn_predict.clicked.connect(self.predict_current)
        action_bar.addWidget(self.btn_predict)

        self.btn_delete = StyledButton("Delete", "#f44336", "#ef5350", "#c62828")
        self.btn_delete.setFixedWidth(140)
        self.btn_delete.clicked.connect(self.delete_current)
        action_bar.addWidget(self.btn_delete)

        self.btn_reset_view = StyledButton("Reset View", "#607d8b", "#78909c", "#455a64")
        self.btn_reset_view.setFixedWidth(150)
        self.btn_reset_view.clicked.connect(self.reset_viewer)
        action_bar.addWidget(self.btn_reset_view)

        self.mode_label = QLabel()
        self.update_mode_label()
        action_bar.addWidget(self.mode_label)

        action_bar.addStretch()
        left_layout.addLayout(action_bar)

        # Viewer frame
        viewer_frame = QFrame()
        viewer_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 3px solid #444;
                border-radius: 12px;
            }
        """)
        viewer_layout = QVBoxLayout(viewer_frame)
        viewer_layout.setContentsMargins(5, 5, 5, 5)
        viewer_frame.setContentsMargins(0, 0, 0, 0)
        viewer_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 3px solid #444;
                border-radius: 12px;
                margin-bottom: 12px;   /* tạo khoảng cách xuống thumbnail */
            }
        """)
        self.viewer = ImageViewer()
        self.viewer.roi_selected.connect(self.on_roi_selected)
        viewer_layout.addWidget(self.viewer)
        
        left_layout.addWidget(viewer_frame, stretch=1)

        # ===== (3) LEFT BOTTOM: thumbnails =====
        self.thumbnail_bar = ThumbnailBar()
        self.thumbnail_bar.image_selected.connect(self.on_image_selected)

        # ===== (2) RIGHT: result panel (span 2 rows) =====
        self.result_panel = ResultPanel()

        result_scroll = QScrollArea()
        result_scroll.setStyleSheet("""
            QScrollArea {
                background-color: rgba(0,0,0,0.25);
                border: 3px solid #444;
                border-radius: 12px;
                margin: 0px;
                padding: 0px;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)
        result_scroll.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        result_scroll.setWidgetResizable(True)
        result_scroll.setFrameShape(QFrame.Shape.NoFrame)
        result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        result_scroll.setWidget(self.result_panel)

        # ===== Fixed sizes you want =====
        RIGHT_PANEL_W = 420      # chỉnh theo ý
        THUMBNAIL_H = 180        # tăng lên => (1) sẽ thấp xuống (đúng ý “ô 1 bớt dài”)

        result_scroll.setFixedWidth(RIGHT_PANEL_W)
        self.thumbnail_bar.setFixedHeight(THUMBNAIL_H)

        # ===== Add to grid =====
        # row 0 col 0: (1)
        grid.addWidget(left_panel, 0, 0)
        grid.addWidget(self.thumbnail_bar, 1, 0)
        # Result chỉ ở hàng 0 (cao bằng viewer)
        grid.addWidget(left_panel, 0, 0)
        grid.addWidget(self.thumbnail_bar, 1, 0)

        # Ô dưới bên phải để trống (để layout cân)
        grid.addWidget(result_scroll, 0, 1, 2, 1)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)



        # ===== Stretch rules =====
        grid.setColumnStretch(0, 1)  # left expands
        grid.setColumnStretch(1, 0)  # right fixed width
        grid.setRowStretch(0, 1)     # top takes remaining
        grid.setRowStretch(1, 0)     # bottom fixed height

        main_layout.addWidget(content, stretch=1)


    def create_toolbar(self):
        """Create the top toolbar."""
        toolbar = QFrame()
        toolbar.setFixedHeight(70)
        toolbar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a5a7a, stop:1 #2a4a6a);
                border-radius: 12px;
                border: 1px solid #4a6a8a;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)
        
        # App title
        title = QLabel("Blood Cell Analyzer")
        title.setStyleSheet("""
            font-size: 20pt;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        """)
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Upload button
        self.btn_upload = StyledButton("Upload Images", "#2196f3", "#42a5f5", "#1976d2")
        self.btn_upload.setFixedWidth(200)
        self.btn_upload.clicked.connect(self.upload_images)
        layout.addWidget(self.btn_upload)
        
        # Settings button
        self.btn_settings = StyledButton("Settings", "#ff9800", "#ffb74d", "#f57c00")
        self.btn_settings.setFixedWidth(150)
        self.btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(self.btn_settings)
        
        return toolbar

    def update_mode_label(self):
        """Update the mode indicator label."""
        mode = cfg.selected_model_mode
        if cfg.is_2_phase():
            color = "#ff9800"
            icon = "🔄"
        else:
            color = "#4caf50"
        
        self.mode_label.setText(f"Mode: {mode}")
        self.mode_label.setStyleSheet(f"""
            color: {color};
            font-size: 11pt;
            font-weight: bold;
            padding: 8px 15px;
            background-color: rgba(0,0,0,0.3);
            border-radius: 8px;
        """)

    def initialize_pipeline(self):
        """Initialize the ML pipeline."""
        try:
            self.pipeline = AnalysisPipeline()
            self.statusBar().showMessage("Pipeline initialized successfully", 3000)
        except Exception as e:
            print(f"Pipeline init error: {e}")
            self.statusBar().showMessage(f"Pipeline error: {e}", 5000)

    def upload_images(self):
        """Open file dialog to upload images."""
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Blood Cell Images", 
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        
        if files:
            os.makedirs(cfg.input_dir, exist_ok=True)
            
            added = 0
            for f in files:
                try:
                    name = os.path.basename(f)
                    dest = os.path.join(cfg.input_dir, name)
                    if not os.path.exists(dest):
                        shutil.copy2(f, dest)
                        added += 1
                except Exception as e:
                    print(f"Error copying {f}: {e}")
            
            if added > 0:
                self.load_input_images()
                self.statusBar().showMessage(f"Added {added} new image(s)", 3000)
            
    def postprocess_edge_boxes(self, results, image_path, margin=4, ratio=0.65):
        if not results:
            return results

        pix = QPixmap(image_path)
        W, H = pix.width(), pix.height()
        if W <= 0 or H <= 0:
            return results

        widths, heights, areas = [], [], []
        for r in results:
            try:
                x1, y1, x2, y2 = r["bbox"]
                w = max(0, x2 - x1)
                h = max(0, y2 - y1)
                if w > 0 and h > 0:
                    widths.append(w)
                    heights.append(h)
                    areas.append(w * h)
            except Exception:
                pass

        if not widths:
            return results

        med_w = median(widths)
        med_h = median(heights)
        med_a = median(areas)

        for r in results:
            try:
                x1, y1, x2, y2 = r["bbox"]
                w = max(0, x2 - x1)
                h = max(0, y2 - y1)
                a = w * h


                touches_border = (
                    x1 <= margin or y1 <= margin or
                    x2 >= (W - margin) or y2 >= (H - margin)
                )

      
                small = (
                    (w < med_w * ratio) or
                    (h < med_h * ratio) or
                    (a < med_a * (ratio ** 2))
                )

                if touches_border and small:
                    if "raw_label" not in r:
                        r["raw_label"] = r.get("label", "Unknown")
                    r["label"] = "Uncertain"
                    r["confidence"] = 0.0
                    r["uncertain_reason"] = "Truncated at image border"
            except Exception:
                continue

        return results


    def open_settings(self):
        """Open the settings dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ Model Settings")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2a3a4a;
            }
            QLabel {
                color: white;
                font-size: 12pt;
            }
            QComboBox {
                background-color: #3a5a7a;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 11pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3a5a7a;
                color: white;
                selection-background-color: #4a7a9a;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Classification Mode")
        title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "• 1 Phase: Direct 5-class classification\n"
            "• 2 Phase: Binary → Stage classification"
        )
        desc.setStyleSheet("font-size: 10pt; color: #aaa;")
        layout.addWidget(desc)
        
        # Mode selector
        combo = QComboBox()
        combo.addItems([cfg.MODEL_MODE_1_PHASE, cfg.MODEL_MODE_2_PHASE])
        combo.setCurrentText(cfg.selected_model_mode)
        layout.addWidget(combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        ok_btn = StyledButton("Apply", "#4caf50", "#66bb6a", "#388e3c")
        ok_btn.clicked.connect(lambda: self.apply_settings(combo.currentText(), dialog))
        btn_layout.addWidget(ok_btn)
        
        cancel_btn = StyledButton("Cancel", "#607d8b", "#78909c", "#455a64")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def apply_settings(self, mode, dialog):
        """Apply settings and close dialog."""
        cfg.set_model_mode(mode)
        self.update_mode_label()
        
        # Clear cached predictions when mode changes
        self.predictions = {}
        
        dialog.accept()
        self.statusBar().showMessage(f"Mode changed to: {mode}", 3000)

    def load_input_images(self):
        """Load images from the input directory."""
        os.makedirs(cfg.input_dir, exist_ok=True)
        
        images = []
        for root, _, files in os.walk(cfg.input_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')):
                    images.append(os.path.join(root, file))
        
        images.sort()
        self.thumbnail_bar.load_images(images)
        
        if images and not self.current_image_path:
            self.on_image_selected(images[0])
        elif not images:
            self.viewer.scene.clear()
            self.result_panel.clear()

    def on_image_selected(self, path):
        """Handle image selection from thumbnail bar."""
        self.current_image_path = path
        self.viewer.load_image(path)

        # Clear ROI selection
        self.result_panel.roi_label.clear()
        self.result_panel.roi_label.setText("Click a cell\nto view")
        self.result_panel.stages_label.setText("Classification:\nSelect a cell...")

        # Check for cached predictions (RAM)
        if path in self.predictions:
            results = self.predictions[path]

            # ====== (C1) POST-PROCESS HERE ======
            results = self.postprocess_edge_boxes(results, path)
            self.predictions[path] = results
            # ====================================

            self.viewer.draw_boxes(results)
            self.result_panel.update_summary(results)
            self.thumbnail_bar.mark_predicted(path)

        else:
            # Check for saved results (DISK)
            cached = self.pipeline.load_cached_results(path) if self.pipeline else None
            if cached:

                # ====== (C2) POST-PROCESS HERE ======
                cached = self.postprocess_edge_boxes(cached, path)
                self.predictions[path] = cached
                # ====================================

                self.viewer.draw_boxes(cached)
                self.result_panel.update_summary(cached)
                self.thumbnail_bar.mark_predicted(path)
            else:
                self.result_panel.update_summary([])

        # Update status
        filename = os.path.basename(path)
        self.statusBar().showMessage(f"Viewing: {filename}")


    def on_roi_selected(self, data, pixmap):
        """Handle ROI selection in the viewer."""
        self.result_panel.update_selection(data, pixmap)

    def predict_current(self):
        """Run prediction on the current image."""
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please select an image first.")
            return
        
        if not self.pipeline:
            self.initialize_pipeline()
            if not self.pipeline:
                QMessageBox.critical(self, "Error", "Failed to initialize pipeline.")
                return
        
        # Disable button during prediction
        self.btn_predict.setEnabled(False)
        self.btn_predict.setText("Processing...")
        
        # Run prediction in background
        self.worker = PredictionWorker(self.pipeline, self.current_image_path)
        self.worker.finished.connect(self.on_prediction_complete)
        self.worker.error.connect(self.on_prediction_error)
        self.worker.start()
    
    def on_prediction_complete(self, results):
        """Handle completed prediction."""
        self.btn_predict.setEnabled(True)
        self.btn_predict.setText("Predict")

        path = self.current_image_path

        # ====== (D) POST-PROCESS HERE ======
        results = self.postprocess_edge_boxes(results, path)
        # ===================================

        self.predictions[path] = results
        self.viewer.draw_boxes(results)
        self.result_panel.update_summary(results)
        self.thumbnail_bar.mark_predicted(path)

        self.statusBar().showMessage(f"Prediction complete: {len(results)} cells detected", 3000)

    
    def on_prediction_error(self, error_msg):
        """Handle prediction error."""
        self.btn_predict.setEnabled(True)
        self.btn_predict.setText("Predict")
        QMessageBox.critical(self, "Prediction Error", f"Failed to run prediction:\n{error_msg}")

    def delete_current(self):
        """Delete the current image."""
        if not self.current_image_path:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Delete {os.path.basename(self.current_image_path)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove file
                if os.path.exists(self.current_image_path):
                    os.remove(self.current_image_path)
                
                # Remove from predictions cache
                if self.current_image_path in self.predictions:
                    del self.predictions[self.current_image_path]
                
                # Reload
                self.current_image_path = None
                self.load_input_images()
                
                self.statusBar().showMessage("Image deleted", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def reset_viewer(self):
        """Reset the image viewer zoom/pan."""
        self.viewer.reset_view()
