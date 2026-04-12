import time
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QLabel, QFrame, QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from .styles import SLIDESHOW_BG_STYLE, OVERLAY_LABEL_STYLE

class SlideshowWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.setWindowTitle("Slideshow")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        
        screen_dis = self.main.screen_dis
        # Find the correct screen
        screens = QApplication.screens()
        target_screen = screens[0]
        if screen_dis - 1 < len(screens):
            target_screen = screens[screen_dis - 1]
            
        self.move(target_screen.geometry().topLeft())
        self.showFullScreen()
        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(SLIDESHOW_BG_STYLE)
        self.setCentralWidget(self.central_widget)
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.central_widget.setLayout(self.layout)
        
        self.views = []
        self.scenes = []
        self.pixmap_items = []
        
        side_count = self.main.side_count
        for i in range(side_count):
            view = QGraphicsView()
            view.setStyleSheet("border: 0px;")
            view.setBackgroundBrush(QColor('#3B3D3F'))
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scene = QGraphicsScene()
            view.setScene(scene)
            view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            pixmap_item = QGraphicsPixmapItem()
            pixmap_item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
            scene.addItem(pixmap_item)
            
            self.views.append(view)
            self.scenes.append(scene)
            self.pixmap_items.append(pixmap_item)
            
            self.layout.addWidget(view)
            
            # Add divider if not last
            if i < side_count - 1:
                divider = QFrame()
                divider.setFrameShape(QFrame.Shape.VLine)
                divider.setFrameShadow(QFrame.Shadow.Plain)
                divider.setStyleSheet("color: #3F4344;")
                divider.setLineWidth(3)
                self.layout.addWidget(divider)
                
        # Overlay labels
        self.lbl_index = QLabel("0/0", self.central_widget)
        self.lbl_index.setStyleSheet(OVERLAY_LABEL_STYLE)
        
        self.lbl_paused = QLabel("", self.central_widget)
        self.lbl_paused.setStyleSheet(OVERLAY_LABEL_STYLE)
        
        self.last_view_time = time.time()
        self.paused = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(300)
        
        # Initial fit after layout settles
        QTimer.singleShot(250, self.update_images)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'lbl_index') and hasattr(self, 'lbl_paused'):
            self.lbl_index.move(self.width() // 2 - self.lbl_index.width() // 2, self.height() - 50)
            self.lbl_index.raise_()
            self.lbl_paused.move(20, 20)
            self.lbl_paused.raise_()
        if hasattr(self, 'pixmap_items') and len(self.pixmap_items) == self.main.side_count:
            QTimer.singleShot(50, self.update_images)
        
    def update_images(self, advance=0):
        if not self.main.filenames: return
        n = self.main.images_len
        side_count = self.main.side_count
        
        self.main.current_index = (self.main.current_index + advance) % n
        
        for i in range(side_count):
            idx = (self.main.current_index + i) % n
            pix = self.main.get_pixmap(idx)
            self.pixmap_items[i].setPixmap(pix)
            if not self.main.save_zoom or not hasattr(self, '_zoomed_once'):
                self.views[i].fitInView(self.pixmap_items[i], Qt.AspectRatioMode.KeepAspectRatio)
                if i == side_count - 1:
                    self._zoomed_once = True
            
        self.lbl_index.setText(f"{self.main.current_index + 1}/{n}")
        self.lbl_index.adjustSize()
        self.lbl_index.move(self.width() // 2 - self.lbl_index.width() // 2, self.height() - 50)
        
    def update_clock(self):
        if not self.paused:
            remaining_time = self.main.slide_show_time - (time.time() - self.last_view_time)
            text = f"{int(remaining_time)}s ({self.main.slide_show_time})"
            self.lbl_paused.setText(text)
            self.lbl_paused.adjustSize()
            
            if remaining_time <= 0:
                self.update_images(self.main.side_count)
                self.last_view_time = time.time()
        else:
            self.lbl_paused.setText(f"Paused ({self.main.slide_show_time})")
            self.lbl_paused.adjustSize()

    def toggle_pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.last_view_time = time.time()
        self.update_clock()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.toggle_pause()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() in (Qt.Key.Key_T, Qt.Key.Key_Space):
            self.toggle_pause()
        elif event.key() == Qt.Key.Key_F:
            self.close()
        elif event.key() == Qt.Key.Key_Left:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.update_images(-1)
            else:
                self.update_images(-self.main.side_count)
            self.last_view_time = time.time()
        elif event.key() == Qt.Key.Key_Right:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.update_images(1)
            else:
                self.update_images(self.main.side_count)
            self.last_view_time = time.time()
        elif event.key() == Qt.Key.Key_J:
            self.update_images(-1)
            self.last_view_time = time.time()
        elif event.key() == Qt.Key.Key_L:
            self.update_images(1)
            self.last_view_time = time.time()
        elif event.key() == Qt.Key.Key_Up:
            self.main.slide_show_time += 1
            self.main.save_settings()
            self.update_clock()
        elif event.key() == Qt.Key.Key_Down:
            if self.main.slide_show_time > 1:
                self.main.slide_show_time -= 1
                self.main.save_settings()
                self.update_clock()
        elif Qt.Key.Key_1 <= event.key() <= Qt.Key.Key_9:
            monitor_idx = event.key() - Qt.Key.Key_1
            screens = QApplication.screens()
            if monitor_idx < len(screens):
                self.main.screen_dis = monitor_idx + 1
                self.main.save_settings()
                self.showNormal()
                target_screen = screens[monitor_idx]
                self.move(target_screen.geometry().topLeft())
                self.showFullScreen()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.update_images(-1)
        else:
            self.update_images(1)
        self.last_view_time = time.time()
        
    def closeEvent(self, event):
        self.main.show()
        if hasattr(self.main, '_pre_slideshow_geometry'):
            self.main.restoreGeometry(self.main._pre_slideshow_geometry)
        self.main.setWindowState(Qt.WindowState.WindowNoState)
        if self.main.internal_ss_active:
            self.main.last_ss_advance_time = time.time()
            self.main.internal_ss_timer.start(500)
        QTimer.singleShot(100, self.main.update_image)
        self.main.raise_()
        self.main.activateWindow()
        super().closeEvent(event)
