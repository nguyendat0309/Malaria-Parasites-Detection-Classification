"""
Image Viewer with interactive bounding boxes.
Color-coded by cell classification stage.
"""

from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                              QGraphicsItem, QGraphicsTextItem, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QPixmap, QPen, QColor, QBrush, QPainter, QFont


class BoundingBoxItem(QGraphicsRectItem):
    """Interactive bounding box for detected cells with stage-specific colors."""
    
    # Distinct color scheme for each cell type
    COLORS = {
        'Healthy': {
            'primary': QColor(34, 197, 94),      # Bright Green
            'hover': QColor(74, 222, 128),
            'hex': '#22c55e'
        },
        'Ring': {
            'primary': QColor(239, 68, 68),      # Bright Red
            'hover': QColor(252, 129, 129),
            'hex': '#ef4444'
        },
        'Trophozoite': {
            'primary': QColor(249, 115, 22),     # Bright Orange
            'hover': QColor(251, 146, 60),
            'hex': '#f97316'
        },
        'Schizont': {
            'primary': QColor(168, 85, 247),     # Purple
            'hover': QColor(192, 132, 252),
            'hex': '#a855f7'
        },
        'Gametocyte': {
            'primary': QColor(59, 130, 246),     # Blue
            'hover': QColor(96, 165, 250),
            'hex': '#3b82f6'
        },
        'Infected': {
            'primary': QColor(239, 68, 68),      # Red (same as Ring)
            'hover': QColor(252, 129, 129),
            'hex': '#ef4444'
        },
        'default': {
            'primary': QColor(251, 191, 36),     # Amber/Yellow
            'hover': QColor(252, 211, 77),
            'hex': '#fbbf24'
        },
        'Uncertain': {
            'primary': QColor(158, 158, 158),   # Gray
            'hover': QColor(189, 189, 189),
            'hex': '#9e9e9e'
        }
    }
    
    def __init__(self, rect, data, callback_click):
        super().__init__(rect)
        self.data = data
        self.callback_click = callback_click
        self.is_selected = False
        
        # Get color based on label
        label = data.get('label', 'default')
        color_info = self.COLORS.get(label, self.COLORS['default'])
        self.base_color = color_info['primary']
        self.hover_color = color_info['hover']
        
        # Style - thicker border for visibility
        pen = QPen(self.base_color, 2)
        pen.setCosmetic(True)
        self.setPen(pen)

        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), 
                                    self.base_color.blue(), 50)))
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setZValue(1)
        
        # Add label text above the box
        self._create_label()
        
    def _create_label(self):
        """Create small label inside top-left of bounding box."""
        label = self.data.get('label', '?')
        conf = self.data.get('confidence', 0) * 100

        short_labels = {
            'Healthy': 'H',
            'Ring': 'R',
            'Trophozoite': 'T',
            'Schizont': 'S',
            'Gametocyte': 'G',
            'Infected': 'I'
        }
        short = short_labels.get(label, '?')
        text = f"{short}:{conf:.0f}%"

        # --- Text item ---
        self.label_text = QGraphicsTextItem(text, self)
        self.label_text.setDefaultTextColor(Qt.GlobalColor.white)

        # Nhỏ hơn + đỡ dày hơn
        font = QFont("Arial", 7, QFont.Weight.DemiBold)
        self.label_text.setFont(font)

        rect = self.rect()

        pad_x = 3
        pad_y = 1

        # đặt trong góc trên-trái của box
        self.label_text.setPos(rect.x() + pad_x, rect.y() + pad_y)
        self.label_text.setZValue(101)



        
    def hoverEnterEvent(self, event):
        pen = QPen(self.hover_color, 3)  
        pen.setCosmetic(True)
        self.setPen(pen)

        self.setBrush(QBrush(QColor(
            self.hover_color.red(),
            self.hover_color.green(),
            self.hover_color.blue(),
            80
        )))

        self.setZValue(10)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        if not self.is_selected:
            pen = QPen(self.base_color, 2)   
            pen.setCosmetic(True)            
            self.setPen(pen)

            self.setBrush(QBrush(QColor(
                self.base_color.red(),
                self.base_color.green(),
                self.base_color.blue(),
                50
            )))

        self.setZValue(1)
        super().hoverLeaveEvent(event)
        
    def select_box(self):
        """Mark this box as selected."""
        self.is_selected = True
        pen = QPen(QColor(0, 255, 255), 3)  
        pen.setCosmetic(True)
        self.setPen(pen)
        self.setBrush(QBrush(QColor(0, 255, 255, 80)))
        self.setZValue(15)
        
    def deselect_box(self):
        """Deselect this box."""
        self.is_selected = False
        pen = QPen(self.base_color, 2)
        pen.setCosmetic(True)
        self.setPen(pen)

        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), 
                                    self.base_color.blue(), 50)))
        self.setZValue(1)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.callback_click(self.data, self)
        super().mousePressEvent(event)


class ImageViewer(QGraphicsView):
    """Image viewer with zoom, pan, and interactive bounding boxes."""
    
    # Signal: ROI data, cropped pixmap
    roi_selected = pyqtSignal(dict, QPixmap)

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Rendering
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Style
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #1a1a2e;
                border: 3px solid #4a5568;
                border-radius: 10px;
            }
        """)
        
        self.current_pixmap = None
        self.pixmap_item = None
        self.bounding_boxes = []
        self.selected_box = None
        
    def load_image(self, image_path):
        self.scene.clear()
        self.bounding_boxes = []
        self.selected_box = None

        self.resetTransform()  # quan trọng: reset zoom/pan cũ

        self.current_pixmap = QPixmap(image_path)
        if not self.current_pixmap.isNull():
            self.pixmap_item = self.scene.addPixmap(self.current_pixmap)

            # Ép sceneRect đúng theo ảnh để tránh bị lệch do bounding rect khác
            self.scene.setSceneRect(self.pixmap_item.boundingRect())

            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.centerOn(self.pixmap_item)  # ép về giữa

            
    def draw_boxes(self, predictions):
        """Draw bounding boxes for predictions with stage-specific colors."""
        # Clear existing boxes (but keep image)
        for box in self.bounding_boxes:
            if box.scene():
                self.scene.removeItem(box)
        self.bounding_boxes = []
        self.selected_box = None
                
        for pred in predictions:
            try:
                x1, y1, x2, y2 = pred["bbox"]
                w = x2 - x1
                h = y2 - y1
                
                # Skip invalid boxes
                if w < 5 or h < 5:
                    continue
                    
                rect = QRectF(0, 0, w, h)               
                box = BoundingBoxItem(rect, pred, self.handle_box_click)
                box.setPos(x1, y1)                        

                self.scene.addItem(box)
                self.bounding_boxes.append(box)
            except Exception as e:
                print(f"Error drawing box {pred}: {e}")
        
        print(f"Drew {len(self.bounding_boxes)} bounding boxes")
        if self.pixmap_item:
            self.scene.setSceneRect(self.pixmap_item.boundingRect())
            self.centerOn(self.pixmap_item)

    def handle_box_click(self, data, box_item):
        """Handle click on a bounding box."""
        # Deselect previous
        if self.selected_box and self.selected_box != box_item:
            self.selected_box.deselect_box()
        
        # Select new
        box_item.select_box()
        self.selected_box = box_item
        
        # Extract ROI from pixmap
        x1, y1, x2, y2 = data["bbox"]
        w = x2 - x1
        h = y2 - y1
        
        if self.current_pixmap:
            roi_pixmap = self.current_pixmap.copy(int(x1), int(y1), int(w), int(h))
            self.roi_selected.emit(data, roi_pixmap)

    def wheelEvent(self, event):
        """Handle zoom with mouse wheel."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Save the scene pos
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

        # Get the new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
    
    def reset_view(self):
        """Reset zoom and pan to fit the image."""
        if self.pixmap_item:
            self.resetTransform()
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
