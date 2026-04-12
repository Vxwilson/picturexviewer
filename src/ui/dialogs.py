import os
import platform
import pickle
import time
from functools import partial
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QCheckBox, QFormLayout, QSpinBox, QListWidget, QComboBox, 
                             QListWidgetItem, QLineEdit, QScrollArea, QMenu, QMessageBox,
                             QFrame, QWidget, QStackedWidget)
from PyQt6.QtGui import QPixmap, QAction, QDesktopServices, QImageReader
from PyQt6.QtCore import Qt, QTimer, QSize, QUrl

from .widgets import RecentItemWidget, ToggleSwitch, SettingRow
from .styles import RECENTS_DIALOG_STYLE, CONTEXT_MENU_STYLE, SETTINGS_DIALOG_STYLE

class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.setWindowTitle("Preferences")
        self.resize(700, 500)
        self.setStyleSheet(SETTINGS_DIALOG_STYLE)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setObjectName("settingsSidebar")
        self.sidebar.setFixedWidth(180)
        self.sidebar.addItems(["General", "Interface", "Viewer", "Slideshow", "History"])
        self.sidebar.currentRowChanged.connect(self.display_page)
        main_layout.addWidget(self.sidebar)
        
        # Content Area
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)
        
        self.init_pages()
        self.sidebar.setCurrentRow(0)
        
    def init_pages(self):
        # Page 1: General
        gen_page = QWidget()
        gen_layout = QVBoxLayout(gen_page)
        gen_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.reopen_images_tg = ToggleSwitch()
        self.reopen_images_tg.setChecked(self.main.reopen_images_bool)
        self.reopen_images_tg.toggled.connect(self.update_settings)
        gen_layout.addWidget(SettingRow("Reopen Last Session", self.reopen_images_tg, "Automatically load images from your previous session on startup."))
        
        self.auto_sort_tg = ToggleSwitch()
        self.auto_sort_tg.setChecked(self.main.auto_sort)
        self.auto_sort_tg.toggled.connect(self.update_settings)
        gen_layout.addWidget(SettingRow("Auto-sort Images", self.auto_sort_tg, "Automatically sort images by name when opening a folder."))
        gen_layout.addStretch()
        
        self.pages.addWidget(gen_page)
        
        # Page 2: Interface
        int_page = QWidget()
        int_layout = QVBoxLayout(int_page)
        int_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.show_label_tg = ToggleSwitch()
        self.show_label_tg.setChecked(self.main.show_label)
        self.show_label_tg.toggled.connect(self.update_settings)
        int_layout.addWidget(SettingRow("Show Image Label", self.show_label_tg, "Display the filename and index overlay at the bottom."))
        int_layout.addStretch()
        
        self.pages.addWidget(int_page)
        
        # Page 3: Viewer
        view_page = QWidget()
        view_layout = QVBoxLayout(view_page)
        view_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.save_zoom_tg = ToggleSwitch()
        self.save_zoom_tg.setChecked(self.main.save_zoom)
        self.save_zoom_tg.toggled.connect(self.update_settings)
        view_layout.addWidget(SettingRow("Persist Zoom", self.save_zoom_tg, "Maintain the current zoom level when switching between images."))
        
        self.auto_fit_tg = ToggleSwitch()
        self.auto_fit_tg.setChecked(self.main.auto_fit_on_nav)
        self.auto_fit_tg.toggled.connect(self.update_settings)
        view_layout.addWidget(SettingRow("Auto-fit on Navigation", self.auto_fit_tg, "Automatically fit each new image to the window when navigating."))
        view_layout.addStretch()
        
        self.pages.addWidget(view_page)
        
        # Page 4: Slideshow
        ss_page = QWidget()
        ss_layout = QVBoxLayout(ss_page)
        ss_layout.setContentsMargins(40, 40, 40, 40)
        ss_layout.setSpacing(15)
        ss_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.ss_time_box = QSpinBox()
        self.ss_time_box.setRange(1, 120)
        self.ss_time_box.setSuffix(" s")
        self.ss_time_box.setValue(self.main.slide_show_time)
        self.ss_time_box.valueChanged.connect(self.update_settings)
        ss_layout.addWidget(SettingRow("Slideshow Interval", self.ss_time_box, "Duration for each image in seconds during slideshow."))
        ss_layout.addStretch()
        
        self.pages.addWidget(ss_page)
        
        # Page 5: History
        hist_page = QWidget()
        hist_layout = QVBoxLayout(hist_page)
        hist_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.save_paths_tg = ToggleSwitch()
        self.save_paths_tg.setChecked(self.main.save_paths)
        self.save_paths_tg.toggled.connect(self.update_settings)
        hist_layout.addWidget(SettingRow("Record History", self.save_paths_tg, "Save recently opened folders and files for quick access."))
        
        self.hide_missing_tg = ToggleSwitch()
        self.hide_missing_tg.setChecked(self.main.hide_missing_recent)
        self.hide_missing_tg.toggled.connect(self.update_settings)
        hist_layout.addWidget(SettingRow("Hide Missing Paths", self.hide_missing_tg, "Automatically hide history items if the files have been moved or deleted."))
        
        self.max_paths_box = QSpinBox()
        self.max_paths_box.setRange(1, 500)
        self.max_paths_box.setValue(self.main.max_recent_paths)
        self.max_paths_box.valueChanged.connect(self.update_settings)
        hist_layout.addWidget(SettingRow("Max History Entries", self.max_paths_box, "Limit the number of recent sessions to store."))
        
        self.thumb_size_box = QSpinBox()
        self.thumb_size_box.setRange(40, 300)
        self.thumb_size_box.setSuffix(" px")
        self.thumb_size_box.setValue(self.main.thumb_size)
        self.thumb_size_box.valueChanged.connect(self.update_settings)
        hist_layout.addWidget(SettingRow("Thumbnail Size", self.thumb_size_box, "Size of the preview thumbnails in the recent sessions gallery."))
        
        hist_layout.addSpacing(20)
        self.reset_btn = QPushButton("Clear All History")
        self.reset_btn.setStyleSheet("background-color: #442222; color: #EEE; padding: 8px; border-radius: 4px; font-weight: bold;")
        self.reset_btn.clicked.connect(self.reset_history)
        hist_layout.addWidget(self.reset_btn)
        hist_layout.addStretch()
        
        self.pages.addWidget(hist_page)

    def display_page(self, index):
        self.pages.setCurrentIndex(index)
        
    def reset_history(self):
        ans = QMessageBox.question(self, "Clear History", "Are you sure you want to clear all history?", 
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            self.main.add_path(clear=True)
            self.main.refresh_paths()

    def update_settings(self):
        self.main.show_label = self.show_label_tg.isChecked()
        self.main.reopen_images_bool = self.reopen_images_tg.isChecked()
        self.main.save_paths = self.save_paths_tg.isChecked()
        self.main.save_zoom = self.save_zoom_tg.isChecked()
        self.main.auto_sort = self.auto_sort_tg.isChecked()
        self.main.hide_missing_recent = self.hide_missing_tg.isChecked()
        self.main.slide_show_time = self.ss_time_box.value()
        self.main.max_recent_paths = self.max_paths_box.value()
        self.main.thumb_size = self.thumb_size_box.value()
        self.main.auto_fit_on_nav = self.auto_fit_tg.isChecked()
        self.main.apply_settings()

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

class RecentPathsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.thumb_size = self.main.thumb_size
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
