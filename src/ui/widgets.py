import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
                             QFrame, QScrollArea)
from PyQt6.QtGui import QPixmap, QIcon, QColor, QWheelEvent, QImageReader, QPainter, QBrush, QPen
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QRect, QPoint
from .styles import SCROLL_AREA_STYLE

class QImageViewer(QGraphicsView):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.pixmap_item = QGraphicsPixmapItem()
        self.pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.pixmap_item)
        
        self.setBackgroundBrush(QColor('#3B3D3F'))
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Ensure drag and drop events bubble up to MainWindow
        self.setAcceptDrops(False)
        
        self.zoom_factor = 1.0
        self.base_zoom_factor = 1.0
        
    def set_image(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(self.pixmap_item.boundingRect())
        
    def fit_image(self):
        if not self.pixmap_item.pixmap().isNull():
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            # Update zoom factor tracking based on current view transform
            self.zoom_factor = self.transform().m11()
            self.base_zoom_factor = self.zoom_factor
            if hasattr(self, 'main'):
                self.main.update_zoom_label(1.0)
            
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier: 
            # Zoom logic
            zoom_in_factor = 1.15
            zoom_out_factor = 1.0 / zoom_in_factor
            
            # Save anchor
            old_pos = self.mapToScene(event.position().toPoint())
            
            if event.angleDelta().y() > 0:
                zoom = zoom_in_factor
            else:
                zoom = zoom_out_factor
                
            self.zoom_factor *= zoom
            self.scale(zoom, zoom)
            
            # Restore anchor
            new_pos = self.mapToScene(event.position().toPoint())
            delta = new_pos - old_pos
            self.translate(delta.x(), delta.y())
            
            if hasattr(self, 'base_zoom_factor') and self.base_zoom_factor != 0:
                relative_zoom = self.zoom_factor / self.base_zoom_factor
            else:
                relative_zoom = 1.0
            self.main.update_zoom_ui(relative_zoom)
        else:
            super().wheelEvent(event)
            
    def set_zoom(self, relative_zoom):
        if hasattr(self, 'base_zoom_factor') and self.base_zoom_factor != 0:
            target_zoom = self.base_zoom_factor * relative_zoom
            current_zoom = self.transform().m11()
            if current_zoom != 0:
                s = target_zoom / current_zoom
                self.scale(s, s)
                self.zoom_factor = target_zoom
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            self._drag_start_pos = event.pos()
        elif event.button() == Qt.MouseButton.RightButton:
            self.main.show_context_menu(event.globalPosition().toPoint())
            
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self, '_drag_start_pos'):
                diff = event.pos() - self._drag_start_pos
                if diff.manhattanLength() < 5:
                    self.main.next_image()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.main.select_images()

class SideBySideWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.viewers = []
        self.update_viewers()

    def update_viewers(self):
        # Clear existing
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.viewers = []
        side_count = self.main.side_count
        for i in range(side_count):
            viewer = QImageViewer(self.main)
            self.layout.addWidget(viewer, stretch=1)
            self.viewers.append(viewer)
            
            if i < side_count - 1:
                divider = QFrame()
                divider.setFrameShape(QFrame.Shape.VLine)
                divider.setFrameShadow(QFrame.Shadow.Plain)
                divider.setStyleSheet("color: #3F4344;")
                divider.setLineWidth(3)
                self.layout.addWidget(divider)
                
    def update_images(self):
        if not self.main.filenames: return
        n = self.main.images_len
        for i, viewer in enumerate(self.viewers):
            idx = (self.main.current_index + i) % n
            pix = self.main.get_pixmap(idx)
            viewer.set_image(pix)
            if not self.main.save_zoom:
                viewer.fit_image()

class InfiniteScrollWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.batch_size = 30
        self.loaded_count = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(SCROLL_AREA_STYLE)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        # Ensure drag and drop events bubble up to MainWindow
        self.scroll_area.setAcceptDrops(False)
        self.scroll_area.viewport().setAcceptDrops(False)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # Debounce timer for index tracking during scroll
        self.tracker_timer = QTimer(self)
        self.tracker_timer.setSingleShot(True)
        self.tracker_timer.timeout.connect(self.calculate_current_index)
        
    def on_scroll(self, value):
        # Auto-load more when near bottom
        bar = self.scroll_area.verticalScrollBar()
        if value > bar.maximum() - 800: # Trigger early for smoothness
            self.load_next_batch()

        # Update current index after a short delay
        self.tracker_timer.start(50)

    def calculate_current_index(self):
        if not self.scroll_content.isVisible(): return
        
        # Geometry-based tracker
        y_scroll = self.scroll_area.verticalScrollBar().value()
        viewport_center_y = y_scroll + self.scroll_area.viewport().height() / 2
        
        found_idx = None
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                geom = widget.geometry()
                if geom.top() <= viewport_center_y <= geom.bottom():
                    found_idx = widget.property("index")
                    break
            
        if found_idx is not None and self.main.current_index != found_idx:
            self.main.current_index = found_idx
            self.main.update_label()
            self.update_selection_highlight()
            
    def update_selection_highlight(self):
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    if widget.property("index") == self.main.current_index:
                        btn.setStyleSheet("border: 3px solid #3574F0; border-radius: 4px; background-color: #000;")
                    else:
                        btn.setStyleSheet("border: 2px solid #333; border-radius: 4px; background-color: #000;")

    def update_view(self, jump_to_current=False):
        if not self.main.filenames: return
        
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.loaded_count = 0
        
        if jump_to_current:
            count_to_load = ((self.main.current_index // self.batch_size) + 1) * self.batch_size
            self.load_next_batch(count_to_load)
            QTimer.singleShot(100, self.scroll_to_current_index)
            QTimer.singleShot(150, self.update_selection_highlight)
        else:
            self.load_next_batch()

    def scroll_to_current_index(self):
        for i in range(self.scroll_layout.count()):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget and widget.property("index") == self.main.current_index:
                self.scroll_area.ensureWidgetVisible(widget)
                break
                
    def load_next_batch(self, count=None):
        total = len(self.main.filenames)
        if self.loaded_count >= total: return
        
        start = self.loaded_count
        batch_to_load = count if count else self.batch_size
        end = min(start + batch_to_load, total)
        self.loaded_count = end
        
        filenames = self.main.filenames
        dpr = self.devicePixelRatio()
        
        zoom_factor = getattr(self.main, 'zoom_slider', None).value() / 100.0 if hasattr(self.main, 'zoom_slider') else 1.0
        
        target_w = self.scroll_area.viewport().width() - 40
        target_h = (self.scroll_area.viewport().height() - 80) * zoom_factor
        if target_w <= 0: target_w = 800
        if target_h <= 0: target_h = 600
        
        for i in range(start, end):
            f_path = filenames[i]
            container = QWidget()
            cont_layout = QVBoxLayout(container)
            cont_layout.setContentsMargins(5, 5, 5, 5)
            
            btn = QPushButton()
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.on_image_clicked(idx))
            btn.setStyleSheet("border: 2px solid #333; border-radius: 4px; background-color: #000;")
            
            if os.path.exists(f_path):
                reader = QImageReader(f_path)
                reader.setAutoTransform(True)
                orig_size = reader.size()
                if orig_size.isValid():
                    w_scale = target_w / orig_size.width()
                    h_scale = target_h / orig_size.height()
                    scale = min(w_scale, h_scale)
                    
                    new_w = int(orig_size.width() * scale)
                    new_h = int(orig_size.height() * scale)
                    
                    reader.setScaledSize(QSize(int(new_w * dpr), int(new_h * dpr)))
                    q_img = reader.read()
                    if not q_img.isNull():
                        pix = QPixmap.fromImage(q_img)
                        pix.setDevicePixelRatio(dpr)
                        btn.setIcon(QIcon(pix))
                        btn.setIconSize(QSize(new_w, new_h))
            
            cont_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            
            name_lbl = QLabel(os.path.basename(f_path))
            name_lbl.setStyleSheet("color: #AAA; font-size: 11px;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cont_layout.addWidget(name_lbl)
            
            container.setProperty("index", i)
            self.scroll_layout.addWidget(container)
        
    def on_image_clicked(self, index):
        self.main.current_index = index
        self.main.update_label()
        self.update_selection_highlight()

    def scroll_next(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() + self.scroll_area.viewport().height())

    def scroll_prev(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() - self.scroll_area.viewport().height())

class RecentItemWidget(QWidget):
    def __init__(self, path_list, exists=True, parent=None):
        super().__init__(parent)
        self.path_list = path_list
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.thumb_lbl = QLabel()
        self.thumb_size = getattr(parent, 'thumb_size', 75)
        self.thumb_lbl.setFixedSize(self.thumb_size, self.thumb_size)
        self.thumb_lbl.setStyleSheet("background-color: #222; border-radius: 4px;")
        self.thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if path_list:
            first_path = path_list[0]
            if os.path.exists(first_path):
                pix = QPixmap(first_path)
                if not pix.isNull():
                    dpr = self.devicePixelRatio()
                    scaled_pix = pix.scaled(int(self.thumb_size * dpr), int(self.thumb_size * dpr), 
                                          Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
                    scaled_pix.setDevicePixelRatio(dpr)
                    self.thumb_lbl.setPixmap(scaled_pix)
            else:
                self.thumb_lbl.setText("❌")
                self.thumb_lbl.setStyleSheet("background-color: #333; border-radius: 4px; color: #666;")
                
        layout.addWidget(self.thumb_lbl)
        
        text_layout = QVBoxLayout()
        if path_list:
            parent_dir = os.path.dirname(path_list[0])
            base_name = os.path.basename(parent_dir) if parent_dir else "Root"
        else:
            base_name = "Unknown"
        self.name_lbl = QLabel(base_name)
        self.name_lbl.setStyleSheet("font-weight: bold; color: #EEE;")
        
        full_path = str(path_list[0]) if path_list else ""
        self.path_lbl = QLabel(full_path)
        self.path_lbl.setStyleSheet("color: #AAA; font-size: 10px;")
        self.path_lbl.setWordWrap(False)
        
        text_layout.addWidget(self.name_lbl)
        text_layout.addWidget(self.path_lbl)
        layout.addLayout(text_layout)
        
        self.count_lbl = QLabel(f"📁 {len(path_list)}")
        self.count_lbl.setStyleSheet("color: #888; font-size: 11px; background-color: rgba(0,0,0,80); padding: 2px 5px; border-radius: 4px;")
        self.count_lbl.setFixedWidth(60) 
        self.count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_lbl, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        
        if not exists:
            self.name_lbl.setStyleSheet("color: #666; font-weight: bold;")
            self.path_lbl.setStyleSheet("color: #444; font-size: 10px;")
            self.setEnabled(False)

class ToggleSwitch(QPushButton):
    def __init__(self, parent=None, width=44, height=22):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._thumb_pos = 2 if not self.isChecked() else self.width() - self.height() + 2
        self._anim = QPropertyAnimation(self, b"thumb_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
    @pyqtProperty(int)
    def thumb_pos(self):
        return self._thumb_pos
        
    @thumb_pos.setter
    def thumb_pos(self, pos):
        self._thumb_pos = pos
        self.update()
        
    def nextCheckState(self):
        super().nextCheckState()
        self._animate_thumb()
        
    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_thumb_pos()

    def _animate_thumb(self):
        start = self._thumb_pos
        end = self.width() - self.height() + 2 if self.isChecked() else 2
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
        
    def _update_thumb_pos(self):
        self._thumb_pos = self.width() - self.height() + 2 if self.isChecked() else 2
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_thumb_pos()
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bg
        brush_color = QColor("#3574F0") if self.isChecked() else QColor("#4F5258")
        p.setBrush(brush_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), self.height() // 2, self.height() // 2)
        
        # Thumb
        p.setBrush(QColor("white"))
        thumb_size = self.height() - 4
        p.drawEllipse(self._thumb_pos, 2, thumb_size, thumb_size)

class SettingRow(QWidget):
    def __init__(self, label_text, control_widget, description=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(2)
        
        top_layout = QHBoxLayout()
        self.label = QLabel(label_text)
        self.label.setStyleSheet("font-size: 13px; font-weight: bold; color: #EEE;")
        
        top_layout.addWidget(self.label)
        top_layout.addStretch()
        top_layout.addWidget(control_widget)
        
        layout.addLayout(top_layout)
        
        if description:
            self.desc_label = QLabel(description)
            self.desc_label.setStyleSheet("font-size: 11px; color: #888;")
            self.desc_label.setWordWrap(True)
            layout.addWidget(self.desc_label)
        
        self.setFixedHeight(self.sizeHint().height())
