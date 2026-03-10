"""
Custom widgets for the Blood Cell Analysis application.
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QScrollArea, QPushButton, QFrame, QGridLayout,
                              QProgressBar, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette, QPainter


class ThumbnailBar(QScrollArea):
    """Horizontal scrollable bar of image thumbnails."""
    
    image_selected = pyqtSignal(str)  # Path

    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setFixedHeight(150)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setStyleSheet("""
            QScrollArea {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3d3d3d, stop:1 #2a2a2a);
                border-top: 3px solid #555;
                border-radius: 0px;
            }
            QScrollBar:horizontal {
                height: 10px;
                background: #333;
            }
            QScrollBar::handle:horizontal {
                background: #666;
                border-radius: 5px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #888;
            }
        """)
        
        self.container = QWidget()
        self.layout = QHBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 10, 15, 10)
        self.setWidget(self.container)
        
        self.thumbnails = {}
        self.current_selection = None
        
    def load_images(self, image_paths):
        """Load thumbnails from image paths."""
        # Clear existing
        for i in reversed(range(self.layout.count())): 
            item = self.layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)
        
        self.thumbnails = {}
        
        for path in image_paths:
            thumb = ThumbnailWidget(path)
            thumb.clicked.connect(self.on_thumb_clicked)
            self.layout.addWidget(thumb)
            self.thumbnails[path] = thumb

    def on_thumb_clicked(self, path):
        """Handle thumbnail click."""
        # Update selection state
        if self.current_selection and self.current_selection in self.thumbnails:
            self.thumbnails[self.current_selection].set_selected(False)
        
        self.current_selection = path
        if path in self.thumbnails:
            self.thumbnails[path].set_selected(True)
        
        self.image_selected.emit(path)
    
    def mark_predicted(self, path):
        """Mark a thumbnail as predicted."""
        if path in self.thumbnails:
            self.thumbnails[path].set_predicted(True)
    
    def remove_image(self, path):
        """Remove a thumbnail."""
        if path in self.thumbnails:
            widget = self.thumbnails[path]
            self.layout.removeWidget(widget)
            widget.setParent(None)
            del self.thumbnails[path]


class ThumbnailWidget(QWidget):
    """Individual thumbnail widget."""
    
    clicked = pyqtSignal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.is_selected = False
        self.is_predicted = False
        
        self.setFixedSize(120, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(110, 90)
        
        # Load and scale pixmap
        pix = QPixmap(path)
        if not pix.isNull():
            self.image_label.setPixmap(
                pix.scaled(106, 86, Qt.AspectRatioMode.KeepAspectRatio, 
                          Qt.TransformationMode.SmoothTransformation)
            )
        
        layout.addWidget(self.image_label)
        
        # Filename label
        filename = os.path.basename(path)
        if len(filename) > 14:
            filename = filename[:11] + "..."
        
        self.name_label = QLabel(filename)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("color: #ccc; font-size: 9px;")
        layout.addWidget(self.name_label)
        
        self.update_style()
        
    def update_style(self):
        """Update widget style based on state."""
        if self.is_selected:
            border_color = "#00bcd4"  # Cyan
            bg = "#1a3a4a"
        elif self.is_predicted:
            border_color = "#4caf50"  # Green
            bg = "#1a3a1a"
        else:
            border_color = "#555"
            bg = "#333"
        
        self.setStyleSheet(f"""
            ThumbnailWidget {{
                background-color: {bg};
                border: 3px solid {border_color};
                border-radius: 8px;
            }}
        """)
        
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background-color: #222;
                border: 1px solid #444;
                border-radius: 4px;
            }}
        """)
        
    def set_selected(self, selected):
        """Set selection state."""
        self.is_selected = selected
        self.update_style()
        
    def set_predicted(self, predicted):
        """Set predicted state."""
        self.is_predicted = predicted
        self.update_style()
        
    def mousePressEvent(self, event):
        self.clicked.emit(self.path)
    
    def enterEvent(self, event):
        if not self.is_selected:
            self.setStyleSheet("""
                ThumbnailWidget {
                    background-color: #404040;
                    border: 3px solid #888;
                    border-radius: 8px;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.update_style()
        super().leaveEvent(event)


class ResultPanel(QWidget):
    """Panel showing classification results and summary."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(360)
        self.setStyleSheet("""
            ResultPanel {
                background: rgba(0,0,0,0.20);
                border: none;
            }
        """)

        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Result")
        header.setStyleSheet("""
            font-size: 22pt;
            font-weight: bold;
            color: white;
            padding-bottom: 10px;
        """)

        layout.addWidget(header)
        
        # ROI Section
        roi_frame = QFrame()
        roi_frame.setFixedWidth(340)
        roi_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #bbb;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        roi_layout = QVBoxLayout(roi_frame)
        
        roi_header = QLabel("Selected ROI")
        roi_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        roi_header.setStyleSheet("font-size: 11pt; color: #666; font-weight: bold; border: none;")
        roi_layout.addWidget(roi_header)
        
        self.roi_label = QLabel()
        self.roi_label.setFixedSize(160, 160)
        self.roi_label.setStyleSheet("""
            background-color: #f5f5f5;
            border: 2px dashed #ccc;
            border-radius: 8px;
        """)
        self.roi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.roi_label.setText("Click a cell\nto view")
        
        roi_container = QHBoxLayout()
        roi_container.addStretch()
        roi_container.addWidget(self.roi_label)
        roi_container.addStretch()
        roi_layout.addLayout(roi_container)
        
        layout.addWidget(roi_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Classification Results
        self.stages_label = QLabel("Classification:\nSelect a cell...")
        self.stages_label.setWordWrap(True)
        self.stages_label.setStyleSheet("""
            font-size: 12pt;
            color: #333;
            border: none;
        """)
        # --- Classification Frame (wrap stages_label) ---
        class_frame = QFrame()
        class_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 10px;
                border: 1px solid #bbb;
            }
        """)

        
        CLASS_BOX_W = 340
        class_frame.setFixedWidth(CLASS_BOX_W)

        self.stages_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        class_layout = QVBoxLayout(class_frame)
        class_layout.setContentsMargins(12, 12, 12, 12)
        class_layout.addWidget(self.stages_label)

        layout.addWidget(class_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        
        # Summary Section
        summary_frame = QFrame()
        summary_frame.setFixedWidth(340)
        summary_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.8);
                border-radius: 10px;
                border: 1px solid #ccc;
                padding: 10px;
            }
        """)
        summary_layout = QVBoxLayout(summary_frame)
        
        summary_header = QLabel("Summary")
        summary_header.setStyleSheet("""
            font-size: 14pt; 
            font-weight: bold;
            color: #2c3e50;
            border: none;
            padding-bottom: 5px;
        """)
        summary_layout.addWidget(summary_header)
        
        self.summary_grid = QGridLayout()
        self.summary_grid.setHorizontalSpacing(10)
        self.summary_grid.setVerticalSpacing(6)
        self.summary_labels = {}
        
        cell_types = [
            ("Healthy", "#4caf50"),
            ("Ring", "#f44336"),
            ("Trophozoite", "#ff9800"),
            ("Schizont", "#9c27b0"),
            ("Gametocyte", "#2196f3"),
            ("Uncertain", "#9e9e9e"),
        ]
        
        row_h = 32  # chiều cao tối thiểu mỗi dòng

        for i, (name, color) in enumerate(cell_types):
            name_label = QLabel(f"{name}:")
            name_label.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 11pt; border: none;"
            )
            name_label.setMinimumHeight(row_h)

            count_label = QLabel("0")
            count_label.setStyleSheet(
                "font-size: 12pt; font-weight: bold; color: #333; border: none;"
            )
            count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            count_label.setMinimumHeight(row_h)

            self.summary_grid.addWidget(name_label, i, 0)
            self.summary_grid.addWidget(count_label, i, 1)
            self.summary_labels[name] = count_label

            # Ép QGridLayout không được co hàng quá nhỏ
            self.summary_grid.setRowMinimumHeight(i, row_h)

        
        summary_layout.addLayout(self.summary_grid)
        
        # Total count
        self.total_label = QLabel("Total: 0 cells")
        self.total_label.setStyleSheet("""
            font-size: 12pt; 
            font-weight: bold; 
            color: #2c3e50;
            margin-top: 10px;
            border: none;
            padding-top: 8px;
            border-top: 1px solid #ddd;
        """)
        summary_layout.addWidget(self.total_label)
        
        layout.addWidget(summary_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        layout.addStretch()

    def update_selection(self, data, roi_pixmap):
        """Update display when a ROI is selected."""
        # Update ROI Image
        self.roi_label.setText("")
        self.roi_label.setPixmap(
            roi_pixmap.scaled(156, 156, Qt.AspectRatioMode.KeepAspectRatio, 
                             Qt.TransformationMode.SmoothTransformation)
        )
        
        # Update classification results
        label = data.get('label', 'Unknown')
        conf_raw = data.get('confidence', 0)

        # ====== HANDLE UNCERTAIN (edge/truncated) ======
        if label == "Uncertain":
            reason = data.get("uncertain_reason", "Cannot determine (edge cell)")
            text = f"""
            <div style="font-size:12pt; line-height:1.35;">
            <div><b>Predicted:</b> Uncertain</div>
            <div style="margin-top:6px; opacity:0.85;">{reason}</div>
            </div>
            """
            self.stages_label.setText(text)
            return
        # ==============================================

        conf = conf_raw * 100

        LABEL_W = 140     
        GAP = 14 
        text = f"""<div style="font-size:12pt; line-height:1.35;">
        <table style="width:100%; border-collapse:collapse;">
        <tr>
            <td style="width:{LABEL_W}px; font-weight:600;">Predicted</td>
            <td style="padding-left:{GAP}px; font-weight:700;">{label}</td>
        </tr>
        <tr>
            <td style="width:{LABEL_W}px; font-weight:600;">Confidence</td>
            <td style="padding-left:{GAP}px;">{conf:.1f}%</td>
        </tr>
        </table>
        </div>"""

        if "probs" in data:
            sorted_probs = sorted(data["probs"].items(), key=lambda item: item[1], reverse=True)
            text += '<div style="margin-top:10px; font-size:11pt;"><b>Probabilities</b></div>'
            text += '<table style="width:100%; border-collapse:collapse; font-size:11pt;">'
            for lbl, prob in sorted_probs:
                if prob > 0.01:
                    bar = "█" * int(prob * 10) + "░" * (10 - int(prob * 10))
                    text += f"""
        <tr>
        <td style="width:{LABEL_W}px; padding-top:3px;">{lbl}</td>
        <td style="padding-left:{GAP}px; padding-top:3px; font-family:Consolas, monospace;">
            <span style="display:inline-block; min-width:120px;">{bar}</span>
            <span style="margin-left:10px;">{prob*100:.0f}%</span>
        </td>
        </tr>
        """
            text += "</table>"


        if 'phase1_result' in data:
            text += f'<div style="margin-top:8px; font-size:10.5pt; opacity:0.9;">Phase 1: {data["phase1_result"]}</div>'

        self.stages_label.setText(text)


    def update_summary(self, all_results):
        """Update the summary counts."""
        counts = {}
        for res in all_results:
            lbl = res['label']
            counts[lbl] = counts.get(lbl, 0) + 1
        
        total = 0
        for name, label in self.summary_labels.items():
            count = counts.get(name, 0)
            label.setText(str(count))
            total += count
        
        self.total_label.setText(f"Total: {total} cells")
    
    def clear(self):
        """Clear all displays."""
        self.roi_label.clear()
        self.roi_label.setText("Click a cell\nto view")
        self.stages_label.setText("Classification:\nSelect a cell...")
        for label in self.summary_labels.values():
            label.setText("0")
        self.total_label.setText("Total: 0 cells")


class StyledButton(QPushButton):
    """Custom styled button with gradient and hover effects."""
    
    def __init__(self, text, color_primary="#FF9F55", color_hover="#FFB070", 
                 color_pressed="#E08040", icon=None):
        super().__init__(text)
        self.color_primary = color_primary
        self.color_hover = color_hover
        self.color_pressed = color_pressed
        
        if icon:
            self.setText(f"{icon} {text}")
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color_primary}, stop:1 {self._darken(color_primary, 0.9)});
                color: white;
                border-radius: 18px;
                padding: 12px 25px;
                font-size: 13pt;
                font-weight: bold;
                border: none;
                text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color_hover}, stop:1 {color_primary});
            }}
            QPushButton:pressed {{
                background: {color_pressed};
            }}
            QPushButton:disabled {{
                background: #888;
                color: #ccc;
            }}
        """)
        
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    @staticmethod
    def _darken(hex_color, factor):
        """Darken a hex color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"
