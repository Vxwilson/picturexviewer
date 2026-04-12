import os
import platform
import pickle
import time
from functools import partial
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QCheckBox, QFormLayout, QSpinBox, QListWidget, 
                             QListWidgetItem, QLineEdit, QScrollArea, QMenu, QMessageBox,
                             QFrame, QWidget)
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices, QImageReader
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl

from .widgets import RecentItemWidget
from .styles import RECENTS_DIALOG_STYLE, CONTEXT_MENU_STYLE

class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setWindowTitle("Settings")
        self.resize(600, 100)
        
        layout = QVBoxLayout()
        check_layout = QHBoxLayout()
        
        self.show_label_chk = QCheckBox("Show image label")
        self.show_label_chk.setChecked(self.main.show_label)
        check_layout.addWidget(self.show_label_chk)
        
        self.reopen_images_chk = QCheckBox("Reopen images upon launch")
        self.reopen_images_chk.setChecked(self.main.reopen_images_bool)
        check_layout.addWidget(self.reopen_images_chk)
        
        self.save_paths_chk = QCheckBox("Save opened file path")
        self.save_paths_chk.setChecked(self.main.save_paths)
        
        self.info_lbl = QLabel("ℹ️")
        self.info_lbl.setToolTip("When unchecked, the app will stop recording new history entries,\nbut existing history will still be preserved.")
        self.info_lbl.setStyleSheet("color: #0078D7; font-weight: bold; cursor: help;")
        
        save_layout = QHBoxLayout()
        save_layout.addWidget(self.save_paths_chk)
        save_layout.addWidget(self.info_lbl)
        save_layout.addStretch()
        check_layout.addLayout(save_layout)
        
        self.save_zoom_chk = QCheckBox("Save zoom resolution")
        self.save_zoom_chk.setChecked(self.main.save_zoom)
        check_layout.addWidget(self.save_zoom_chk)
        
        self.auto_sort_chk = QCheckBox("Sort images by name")
        self.auto_sort_chk.setChecked(self.main.auto_sort)
        check_layout.addWidget(self.auto_sort_chk)
        
        layout.addLayout(check_layout)
        
        btn_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset History")
        self.reset_btn.clicked.connect(self.reset_history)
        btn_layout.addWidget(self.reset_btn)
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        btn_layout.addWidget(self.apply_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
    def reset_history(self):
        self.main.add_path(clear=True)
        
    def apply_settings(self):
        self.main.show_label = self.show_label_chk.isChecked()
        self.main.reopen_images_bool = self.reopen_images_chk.isChecked()
        self.main.save_paths = self.save_paths_chk.isChecked()
        self.main.save_zoom = self.save_zoom_chk.isChecked()
        self.main.auto_sort = self.auto_sort_chk.isChecked()
        self.main.apply_settings()
        self.accept()

class ExifDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("EXIF")
        self.resize(300, 200)
        layout = QFormLayout()
        
        self.dimension_lbl = QLabel("-")
        self.model_lbl = QLabel("-")
        self.date_lbl = QLabel("-")
        self.focal_lbl = QLabel("-")
        self.misc_lbl = QLabel("-")
        
        layout.addRow("Dimensions:", self.dimension_lbl)
        layout.addRow("Model:", self.model_lbl)
        layout.addRow("Date taken:", self.date_lbl)
        layout.addRow("Focal length(mm):", self.focal_lbl)
        layout.addRow("Misc:", self.misc_lbl)
        
        self.setLayout(layout)
        self.populate_exif(main_window)

    def populate_exif(self, main):
        exif = main.get_exif(main.current_index)
        if not exif:
            try:
                pix = main.get_pixmap(main.current_index)
                if not pix.isNull():
                    self.dimension_lbl.setText(f"{pix.width()}x{pix.height()}")
            except:
                pass
            return
            
        if 256 in exif and 257 in exif:
            self.dimension_lbl.setText(f"{exif[256]}x{exif[257]}")
        else:
            try:
                pix = main.get_pixmap(main.current_index)
                if not pix.isNull():
                    self.dimension_lbl.setText(f"{pix.width()}x{pix.height()}")
            except:
                pass
                
        if 272 in exif:
            self.model_lbl.setText(str(exif[272]))
        if 306 in exif:
            self.date_lbl.setText(str(exif[306]))
        elif 36867 in exif:
            self.date_lbl.setText(str(exif[36867]))
        if 37386 in exif:
            self.focal_lbl.setText(str(exif[37386]))
        if 39321 in exif:
            self.misc_lbl.setText(str(exif[39321]))

class SlideshowInitiator(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setWindowTitle("Start Slideshow")
        self.resize(400, 90)
        
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Timer (s):"))
        self.timer_box = QSpinBox()
        self.timer_box.setRange(1, 120)
        self.timer_box.setValue(self.main.slide_show_time)
        layout.addWidget(self.timer_box)
        
        layout.addWidget(QLabel("Side by side:"))
        self.side_box = QSpinBox()
        self.side_box.setRange(1, 3)
        self.side_box.setValue(self.main.side_count)
        layout.addWidget(self.side_box)
        
        screens = main_window.app_instance.screens() if hasattr(main_window, 'app_instance') else []
        if len(screens) > 1:
            layout.addWidget(QLabel("Display Monitor:"))
            self.monitor_box = QSpinBox()
            self.monitor_box.setRange(1, len(screens))
            self.monitor_box.setValue(self.main.screen_dis)
            layout.addWidget(self.monitor_box)
        else:
            self.monitor_box = None
            
        btn_start = QPushButton("Start")
        btn_start.clicked.connect(self.start_slideshow)
        layout.addWidget(btn_start)
        
        self.setLayout(layout)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.start_slideshow()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
            
    def start_slideshow(self):
        self.main.slide_show_time = self.timer_box.value()
        self.main.side_count = self.side_box.value()
        if self.monitor_box:
            self.main.screen_dis = self.monitor_box.value()
        self.main.save_settings()
        
        self.accept()
        self.main.open_fs_slideshow()

class RecentPathsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.thumb_size = 75 
        self.batch_size = 30
        self.loaded_count = 0
        self.current_path_list = []
        
        self.setWindowTitle("Recent Sessions")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(RECENTS_DIALOG_STYLE)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search reach sessions by path or filename...")
        self.search_bar.textChanged.connect(self.filter_list)
        header_layout.addWidget(self.search_bar, stretch=2)
        
        self.hide_missing_chk = QCheckBox("Hide missing paths")
        self.hide_missing_chk.setChecked(self.main.hide_missing_recent)
        self.hide_missing_chk.stateChanged.connect(self.toggle_hide_missing)
        header_layout.addWidget(self.hide_missing_chk)
        
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._on_preview_timer_timeout)
        
        content_layout = QHBoxLayout()
        
        self.list_widget = QListWidget()
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.list_widget.itemDoubleClicked.connect(self.load_selected)
        self.list_widget.currentItemChanged.connect(self.trigger_preview_update)
        content_layout.addWidget(self.list_widget, stretch=3)
        
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("previewFrame")
        self.preview_frame.setMinimumWidth(400)
        self.preview_vbox = QVBoxLayout(self.preview_frame)
        self.preview_vbox.setContentsMargins(10, 10, 10, 10)
        
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #888; font-size: 11px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_vbox.addWidget(self.status_lbl)
        self.status_lbl.setVisible(False)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        self.preview_vbox.addWidget(self.scroll_area)
        
        self.empty_lbl = QLabel("Select a session to preview")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666; font-size: 14px;")
        self.preview_vbox.addWidget(self.empty_lbl)
        
        content_layout.addWidget(self.preview_frame, stretch=2)
        main_layout.addLayout(content_layout)
        
        btn_row = QHBoxLayout()
        self.btn_clear_all = QPushButton("Clear History")
        self.btn_clear_all.setObjectName("dangerBtn")
        self.btn_clear_all.clicked.connect(self.clear_all_history)
        btn_row.addWidget(self.btn_clear_all)
        
        btn_row.addStretch()
        
        self.btn_load = QPushButton("Load Selected")
        self.btn_load.clicked.connect(self.load_selected)
        btn_row.addWidget(self.btn_load)
        main_layout.addLayout(btn_row)
        
        self.populate_list()
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self.list_widget.setFocus()
        
    def filter_list(self):
        query = self.search_bar.text().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                match = query in widget.path_lbl.text().lower() or query in widget.name_lbl.text().lower()
                item.setHidden(not match)

    def toggle_hide_missing(self, state):
        self.main.hide_missing_recent = self.hide_missing_chk.isChecked()
        self.main.save_settings()
        self.populate_list()
        
    def populate_list(self):
        self.list_widget.clear()
        for entry in self.main.paths:
            path_list = entry.get('path', [])
            if not path_list: continue
            
            exists = os.path.exists(path_list[0])
            if not exists and self.main.hide_missing_recent:
                continue
                
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(100, self.thumb_size + 12))
            
            widget = RecentItemWidget(path_list, exists, self)
            self.list_widget.setItemWidget(item, widget)
            
            if not exists:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        
        if self.search_bar.text():
            self.filter_list()

    def show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item: return
        
        widget = self.list_widget.itemWidget(item)
        if not widget: return
        
        menu = QMenu(self)
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        
        reveal_action = QAction("Reveal in Finder" if platform.system() == 'Darwin' else "Open Folder", self)
        reveal_action.triggered.connect(partial(self.reveal_path, widget.path_list[0]))
        menu.addAction(reveal_action)
        
        remove_action = QAction("Remove from History", self)
        remove_action.triggered.connect(partial(self.remove_entry, widget.path_list))
        menu.addAction(remove_action)
        
        menu.exec(self.list_widget.viewport().mapToGlobal(pos))
        
    def reveal_path(self, path):
        if os.path.exists(path):
            if platform.system() == 'Darwin':
                import subprocess
                subprocess.run(['open', '-R', path])
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))

    def remove_entry(self, path_list):
        self.main.paths = [p for p in self.main.paths if p.get('path') != path_list]
        # data path adjustment handled in main_window/logic_manager
        self.main.save_paths_data() 
        self.main.update_recents_visibility()
        self.main.refresh_paths()
        self.populate_list()
        
    def clear_all_history(self):
        ans = QMessageBox.question(self, "Clear History", "Are you sure you want to clear all history?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            self.main.add_path(clear=True)
            self.main.refresh_paths()
            self.populate_list()

    def load_selected(self):
        current_item = self.list_widget.currentItem()
        if not current_item: return
        
        widget = self.list_widget.itemWidget(current_item)
        if widget and widget.path_list:
            if os.path.exists(widget.path_list[0]):
                self.main.read_im(widget.path_list)
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Path no longer exists.")
                self.populate_list()

    def trigger_preview_update(self, current, previous):
        self._preview_timer.stop()
        self._preview_timer.start(200)
        
    def _on_preview_timer_timeout(self):
        current_item = self.list_widget.currentItem()
        self.update_preview(current_item, None)

    def update_preview(self, current, previous):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not current:
            self.empty_lbl.setVisible(True)
            self.status_lbl.setVisible(False)
            return
            
        widget = self.list_widget.itemWidget(current)
        if not widget or not widget.path_list:
            return
            
        self.empty_lbl.setVisible(False)
        self.status_lbl.setVisible(True)
        self.current_path_list = widget.path_list
        self.loaded_count = 0
        
        self.load_next_batch(count=1)
        QTimer.singleShot(100, self.seed_preview)
        QTimer.singleShot(10, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def seed_preview(self):
        if not self.current_path_list: return
        bar = self.scroll_area.verticalScrollBar()
        if bar.maximum() == 0 and self.loaded_count < len(self.current_path_list):
            self.load_next_batch(count=5)
        
    def on_scroll(self, value):
        if not self.current_path_list: return
        bar = self.scroll_area.verticalScrollBar()
        if value > bar.maximum() - 600: 
            self.load_next_batch()

    def load_next_batch(self, count=None):
        total = len(self.current_path_list)
        if self.loaded_count >= total: 
            if total > 0:
                self.status_lbl.setText(f"End of session ({total} images)")
            return
        
        start = self.loaded_count
        batch_to_load = count if count else self.batch_size
        end = min(start + batch_to_load, total)
        self.loaded_count = end
        
        dpr = self.devicePixelRatio()
        target_w = self.preview_frame.width() - 40 
        batch = self.current_path_list[start:end]
        
        for p in batch:
            lbl = QLabel()
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setObjectName("previewThumb")
            if os.path.exists(p):
                reader = QImageReader(p)
                reader.setAutoTransform(True)
                orig_size = reader.size()
                if not orig_size.isValid(): continue
                
                tr_w = target_w * dpr
                new_h = int((tr_w / orig_size.width()) * orig_size.height())
                reader.setScaledSize(QSize(int(tr_w), new_h))
                
                q_img = reader.read()
                if not q_img.isNull():
                    pix = QPixmap.fromImage(q_img)
                    pix.setDevicePixelRatio(dpr)
                    lbl.setPixmap(pix)
                else:
                    lbl.setText(f"[Decode error: {os.path.basename(p)}]")
                    lbl.setStyleSheet("color: #666; padding: 20px; background: #222; border-radius: 4px;")
            else:
                lbl.setText(f"[Missing: {os.path.basename(p)}]")
                lbl.setStyleSheet("color: #444; padding: 20px; background: #222; border-radius: 4px;")
            
            self.scroll_layout.addWidget(lbl)
        self.status_lbl.setText(f"Showing {self.loaded_count} of {total}")
