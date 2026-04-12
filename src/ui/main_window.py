import os
import time
from functools import partial
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QStackedWidget, QSlider,
                             QMessageBox, QMenu)
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices, QIcon
from PyQt6.QtCore import Qt, QTimer, QUrl

from ..constants import ViewMode, CURRENT_VERSION, CURRENT_OS, DEFAULT_SLIDE_SHOW_TIME, DEFAULT_SIDE_COUNT, DEFAULT_SCREEN_DIS, MAX_RECENT_PATHS
from .styles import (MAIN_WINDOW_STYLE, FOOTER_FRAME_STYLE, OVERLAY_LABEL_STYLE, 
                    ZEN_ZOOM_OVERLAY_STYLE, ZEN_ZOOM_ICON_STYLE, ZEN_SLIDER_STYLE, 
                    ZEN_STATUS_OVERLAY_STYLE, CONTEXT_MENU_STYLE)
from .widgets import QImageViewer, SideBySideWidget, InfiniteScrollWidget
from .dialogs import SettingsDialog, ExifDialog, SlideshowInitiator, RecentPathsDialog
from .slideshow_window import SlideshowWindow
from ..core.logic_manager import LogicManager

class MainWindow(QMainWindow):
    def __init__(self, app_instance):
        super().__init__()
        self.app_instance = app_instance
        self.logic_manager = LogicManager()
        
        self.setWindowTitle(CURRENT_VERSION)
        
        # Default size: 70% screen width, 80% height
        screen = self.app_instance.primaryScreen().geometry()
        w = int(screen.width() * 0.7)
        h = int(screen.height() * 0.8)
        self.resize(w, h)
        
        # Center on screen
        qr = self.frameGeometry()
        cp = self.app_instance.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
        # State
        self.filenames = []
        self.original_filenames = []
        self.current_index = 0
        self.images_len = 0
        self.sort_mode = 'name'
        
        # Load Data
        self.settings_data = self.logic_manager.load_settings()
        
        self.show_label = self.settings_data.get("show_label", True)
        self.reopen_images_bool = self.settings_data.get("reopen_images", True)
        self.save_paths = self.settings_data.get("save_paths", True)
        self.save_zoom = self.settings_data.get("save_zoom", True)
        self.auto_sort = self.settings_data.get("auto_sort", True)
        self.hide_missing_recent = self.settings_data.get("hide_missing_recent", False)
        
        self.slide_show_time = self.settings_data.get("slide_show_time", DEFAULT_SLIDE_SHOW_TIME)
        self.side_count = self.settings_data.get("side_count", DEFAULT_SIDE_COUNT)
        self.screen_dis = self.settings_data.get("screen_dis", DEFAULT_SCREEN_DIS)
        self.view_mode = self.settings_data.get("view_mode", ViewMode.STANDARD)
        
        self.save_data = self.logic_manager.load_data(self.reopen_images_bool)
        self.paths = self.logic_manager.load_paths()
        
        if self.reopen_images_bool and self.save_data:
            self.filenames = self.save_data.get("filenames", [])
            self.images_len = len(self.filenames)
            self.current_index = self.save_data.get("current_index", 0)
            self.original_filenames = list(self.filenames)
        
        # Internal Slideshow State
        self.internal_ss_active = False
        self.internal_ss_paused = False
        self.internal_ss_timer = QTimer(self)
        self.internal_ss_timer.timeout.connect(self.update_ss_clock)
        self.last_ss_advance_time = 0
        
        self.init_ui()
        self.init_menu()
        
        self.setAcceptDrops(True)
        self.update_recents_visibility()
        
        # Initial load call
        QTimer.singleShot(400, self.initial_startup_load)
            
    def init_ui(self):
        # Set Application Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets', 'Icon', 'picturexviewer.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setAcceptDrops(False) 
        self.main_layout.addWidget(self.stacked_widget, stretch=1)
        
        self.standard_view = QImageViewer(self)
        self.side_by_side_view = SideBySideWidget(self)
        self.infinite_scroll_view = InfiniteScrollWidget(self)
        
        self.stacked_widget.addWidget(self.standard_view) # Index 0
        self.stacked_widget.addWidget(self.side_by_side_view) # Index 1
        self.stacked_widget.addWidget(self.infinite_scroll_view) # Index 2
        
        self.image_viewer = self.standard_view
        
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("color: #81878B; font-size: 11px; font-weight: bold;")
        self.name_label.hide()

        self.ss_status_overlay = QLabel("", self)
        self.ss_status_overlay.setStyleSheet(ZEN_STATUS_OVERLAY_STYLE)
        self.ss_status_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ss_status_overlay.hide()
        
        # Bottom controls
        self.bottom_frame = QFrame()
        self.bottom_frame.setFixedHeight(45)
        self.bottom_frame.setStyleSheet(FOOTER_FRAME_STYLE)
        self.bottom_layout = QHBoxLayout(self.bottom_frame)
        self.bottom_layout.setContentsMargins(10, 0, 10, 0)
        self.bottom_layout.setSpacing(10)
        
        self.btn_open = QPushButton("📁 Open")
        self.btn_open.clicked.connect(self.select_images)
        self.btn_open.setToolTip("Open Folder or Images")
        self.bottom_layout.addWidget(self.btn_open)
        
        self.btn_recents = QPushButton("🕒")
        self.btn_recents.setFixedWidth(40)
        self.btn_recents.clicked.connect(self.open_recents_dialog)
        self.btn_recents.setToolTip("Recent Sessions")
        self.bottom_layout.addWidget(self.btn_recents)

        s_text = "Name" if self.auto_sort else "Default"
        self.btn_sort = QPushButton(f"⇅ {s_text}")
        self.btn_sort.clicked.connect(self.toggle_sort)
        self.btn_sort.setToolTip("Toggle Sort Mode")
        self.bottom_layout.addWidget(self.btn_sort)
        self.bottom_layout.addWidget(self.name_label)
        self.bottom_layout.addStretch()
        
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedWidth(40)
        self.btn_prev.clicked.connect(self.prev_image)
        self.bottom_layout.addWidget(self.btn_prev)
        
        self.lbl_index = QLabel("0/0")
        self.lbl_index.setStyleSheet("color: #81878B; font-weight: bold; min-width: 50px;")
        self.lbl_index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_layout.addWidget(self.lbl_index)
        
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedWidth(40)
        self.btn_next.clicked.connect(self.next_image)
        self.bottom_layout.addWidget(self.btn_next)
        
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("color: #EEE; font-weight: bold; min-width: 40px;")
        self.bottom_layout.addWidget(self.lbl_zoom)
        
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(120)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        self.bottom_layout.addWidget(self.zoom_slider)
        
        self.btn_reset_zoom = QPushButton("⟲")
        self.btn_reset_zoom.setFixedWidth(40)
        self.btn_reset_zoom.setToolTip("Reset Zoom [0]")
        self.btn_reset_zoom.clicked.connect(self.reset_zoom)
        self.bottom_layout.addWidget(self.btn_reset_zoom)
        
        # Zen Mode Overlay
        self.zoom_overlay = QFrame(self)
        self.zoom_overlay.setStyleSheet(ZEN_ZOOM_OVERLAY_STYLE)
        self.zoom_overlay.setFixedHeight(45)
        self.zoom_overlay_layout = QHBoxLayout(self.zoom_overlay)
        self.zoom_overlay_layout.setContentsMargins(15, 0, 15, 0)
        self.zoom_overlay_layout.setSpacing(10)
        
        self.zoom_overlay_icon = QPushButton("🔍")
        self.zoom_overlay_icon.setFlat(True)
        self.zoom_overlay_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.zoom_overlay_icon.setToolTip("Reset Zoom to 100%")
        self.zoom_overlay_icon.clicked.connect(self.reset_zoom)
        self.zoom_overlay_icon.setStyleSheet(ZEN_ZOOM_ICON_STYLE)
        self.zoom_overlay_layout.addWidget(self.zoom_overlay_icon)
        
        self.zoom_slider_ss = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider_ss.setRange(10, 500)
        self.zoom_slider_ss.setValue(self.zoom_slider.value())
        self.zoom_slider_ss.setFixedWidth(180) 
        self.zoom_slider_ss.setStyleSheet(ZEN_SLIDER_STYLE)
        self.zoom_slider_ss.valueChanged.connect(self.on_zoom_slider_changed)
        self.zoom_overlay_layout.addWidget(self.zoom_slider_ss)
        
        self.zoom_lbl_ss = QLabel("100%")
        self.zoom_lbl_ss.setStyleSheet("color: #EEE; min-width: 45px; background: transparent; border: none; font-size: 12px; font-weight: bold;")
        self.zoom_overlay_layout.addWidget(self.zoom_lbl_ss)
        self.zoom_overlay.hide()
        
        self.bottom_layout.addStretch()
        
        self.mode_btn_group = QHBoxLayout()
        self.mode_btn_group.setSpacing(1)
        self.mode_btn_group.setContentsMargins(0, 0, 0, 0)
        
        self.btn_mode_std = QPushButton("⧠")
        self.btn_mode_std.setFixedWidth(40)
        self.btn_mode_std.setToolTip("Standard View [1]")
        self.btn_mode_std.clicked.connect(lambda: self.switch_mode(ViewMode.STANDARD))
        self.btn_mode_std.setStyleSheet("border-top-right-radius: 0; border-bottom-right-radius: 0; border-top-left-radius: 12px; border-bottom-left-radius: 12px;")
        
        self.btn_mode_sbs = QPushButton(f"⧉ {self.side_count}")
        self.btn_mode_sbs.setFixedWidth(50)
        self.btn_mode_sbs.setToolTip("Side-by-Side [2] (Click again to toggle 3)")
        self.btn_mode_sbs.clicked.connect(lambda: self.switch_mode(ViewMode.SIDE_BY_SIDE))
        self.btn_mode_sbs.setStyleSheet("border-radius: 0;")
        
        self.btn_mode_scroll = QPushButton("☰")
        self.btn_mode_scroll.setFixedWidth(40)
        self.btn_mode_scroll.setStyleSheet("border-top-left-radius: 0; border-bottom-left-radius: 0; border-top-right-radius: 12px; border-bottom-right-radius: 12px;")
        self.btn_mode_scroll.setToolTip("Infinite Scroll [3]")
        self.btn_mode_scroll.clicked.connect(lambda: self.switch_mode(ViewMode.INFINITE_SCROLL))
        
        self.mode_btn_group.addWidget(self.btn_mode_std)
        self.mode_btn_group.addWidget(self.btn_mode_sbs)
        self.mode_btn_group.addWidget(self.btn_mode_scroll)
        self.bottom_layout.addLayout(self.mode_btn_group)
        
        self.bottom_layout.addStretch()
        
        self.btn_slideshow = QPushButton("📽 Full")
        self.btn_slideshow.setToolTip("Fullscreen Slideshow [S]")
        self.btn_slideshow.clicked.connect(self.open_slideshow_initiator)
        self.bottom_layout.addWidget(self.btn_slideshow)

        self.btn_toggle_ss = QPushButton("▶")
        self.btn_toggle_ss.setFixedWidth(35)
        self.btn_toggle_ss.setToolTip("Start Internal Slideshow [Alt+Shift+S]")
        self.btn_toggle_ss.clicked.connect(self.toggle_internal_slideshow)
        self.bottom_layout.addWidget(self.btn_toggle_ss)
        
        self.main_layout.addWidget(self.bottom_frame)
        
    def initial_startup_load(self):
        if self.filenames:
            self.read_im(self.filenames, self.current_index)
        self.switch_mode(self.view_mode)
        QTimer.singleShot(100, self.reset_zoom)
        
    def init_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Read from file", self)
        open_action.setShortcuts(["Ctrl+O", "O"])
        open_action.triggered.connect(self.select_images)
        file_menu.addAction(open_action)
        
        self.recent_menu = file_menu.addMenu("Open recent")
        self.refresh_paths()
        file_menu.addSeparator()
        
        pref_action = QAction("Preferences", self)
        pref_action.setShortcut("Alt+P")
        pref_action.triggered.connect(self.open_settings)
        file_menu.addAction(pref_action)
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+X")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        action_menu = menubar.addMenu("Actions")
        self.next_action = QAction("Next", self)
        self.next_action.setShortcuts([">", "Right"])
        self.next_action.triggered.connect(lambda: self.next_image())
        self.addAction(self.next_action)
        action_menu.addAction(self.next_action)
        
        self.prev_action = QAction("Previous", self)
        self.prev_action.setShortcuts(["<", "Left"])
        self.prev_action.triggered.connect(lambda: self.prev_image())
        self.addAction(self.prev_action)
        action_menu.addAction(self.prev_action)
        
        ss_action = QAction("Start Slideshow", self)
        ss_action.setShortcut("S")
        ss_action.triggered.connect(self.open_slideshow_initiator)
        action_menu.addAction(ss_action)
        
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.open_help)
        help_menu.addAction(about_action)
        
        self.shortcut_exif = QAction("Show Exif", self)
        self.shortcut_exif.setShortcut("Ctrl+E")
        self.shortcut_exif.triggered.connect(self.show_exif_dialog)
        self.addAction(self.shortcut_exif)
        
        sort_action = QAction("Toggle Sort", self)
        sort_action.setShortcuts(["Alt+S", "Ctrl+S"])
        sort_action.triggered.connect(self.toggle_sort)
        self.addAction(sort_action)
        
        ss_toggle_action = QAction("Toggle Internal Slideshow", self)
        ss_toggle_action.setShortcut("Alt+Shift+S")
        ss_toggle_action.triggered.connect(self.toggle_internal_slideshow)
        self.addAction(ss_toggle_action)
        
        # J/L Shortcuts for 1x shift
        self.shortcut_j = QAction(self)
        self.shortcut_j.setShortcut("J")
        self.shortcut_j.triggered.connect(lambda: self.prev_image(1))
        self.addAction(self.shortcut_j)
        
        self.shortcut_l = QAction(self)
        self.shortcut_l.setShortcut("L")
        self.shortcut_l.triggered.connect(lambda: self.next_image(1))
        self.addAction(self.shortcut_l)
        
        self.shortcut_ctrl_left = QAction(self)
        self.shortcut_ctrl_left.setShortcut("Ctrl+Left")
        self.shortcut_ctrl_left.triggered.connect(lambda: self.prev_image(1))
        self.addAction(self.shortcut_ctrl_left)
        
        self.shortcut_ctrl_right = QAction(self)
        self.shortcut_ctrl_right.setShortcut("Ctrl+Right")
        self.shortcut_ctrl_right.triggered.connect(lambda: self.next_image(1))
        self.addAction(self.shortcut_ctrl_right)
        
        self.shortcut_up = QAction(self)
        self.shortcut_up.setShortcut("Up")
        self.shortcut_up.triggered.connect(self.timer_up)
        self.addAction(self.shortcut_up)
        
        self.shortcut_down = QAction(self)
        self.shortcut_down.setShortcut("Down")
        self.shortcut_down.triggered.connect(self.timer_down)
        self.addAction(self.shortcut_down)
        
        # View Mode Shortcuts
        self.mode_1 = QAction(self)
        self.mode_1.setShortcut("1")
        self.mode_1.triggered.connect(lambda: self.switch_mode(ViewMode.STANDARD))
        self.addAction(self.mode_1)
        
        self.mode_2 = QAction(self)
        self.mode_2.setShortcut("2")
        self.mode_2.triggered.connect(lambda: self.switch_mode(ViewMode.SIDE_BY_SIDE))
        self.addAction(self.mode_2)
        
        self.mode_3 = QAction(self)
        self.mode_3.setShortcut("3")
        self.mode_3.triggered.connect(lambda: self.switch_mode(ViewMode.INFINITE_SCROLL))
        self.addAction(self.mode_3)
        
        # Zoom Shortcut
        self.shortcut_zero = QAction(self)
        self.shortcut_zero.setShortcut("0")
        self.shortcut_zero.triggered.connect(self.reset_zoom)
        self.addAction(self.shortcut_zero)
        
    def timer_up(self):
        if self.internal_ss_active:
            self.slide_show_time += 1
            self.save_settings()
            self.update_ss_clock()

    def timer_down(self):
        if self.internal_ss_active and self.slide_show_time > 1:
            self.slide_show_time -= 1
            self.save_settings()
            self.update_ss_clock()
        
    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        context_menu.setStyleSheet(CONTEXT_MENU_STYLE)
        exif_action = QAction("Show Exif", self)
        exif_action.setShortcut("Ctrl+E")
        exif_action.triggered.connect(self.show_exif_dialog)
        context_menu.addAction(exif_action)
        
        ss_action = QAction("Start Slideshow", self)
        ss_action.triggered.connect(self.open_slideshow_initiator)
        context_menu.addAction(ss_action)
        context_menu.exec(pos)
        
    def show_exif_dialog(self):
        dlg = ExifDialog(self)
        dlg.exec()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.internal_ss_active:
            self._reposition_overlay()
        self.reset_zoom()
                
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = []
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if local_path and os.path.exists(local_path):
                norm_path = os.path.abspath(os.path.normpath(local_path))
                paths.append(norm_path)
        if paths:
            self.process_dropped_paths(paths)

    def process_dropped_paths(self, paths):
        unique_images = self.logic_manager.scan_for_images(paths)
        if unique_images:
            self.load_files(unique_images)

    def load_files(self, files):
        if not files: return
        self.original_filenames = list(files)
        self.apply_sorting()
        if self.save_paths:
            self.add_path(self.filenames)
        self.refresh_paths()
        self.read_im(self.filenames, 0)
                
    def save_settings(self):
        data = {
            'show_label': self.show_label,
            'reopen_images': self.reopen_images_bool,
            'save_paths': self.save_paths,
            'save_zoom': self.save_zoom,
            'slide_show_time': self.slide_show_time,
            'side_count': self.side_count,
            'screen_dis': self.screen_dis,
            'auto_sort': self.auto_sort,
            'hide_missing_recent': self.hide_missing_recent,
            'view_mode': int(self.view_mode)
        }
        self.logic_manager.save_settings(data)
        self.save_data_now()
            
    def apply_settings(self):
        self.save_settings()
        self.name_label.setVisible(self.show_label)
        self.refresh_paths()
        self.update_label()
        if hasattr(self, 'side_by_side_view'):
            self.side_by_side_view.update_viewers()
            self.side_by_side_view.update_images()

    def switch_mode(self, mode):
        if self.view_mode == ViewMode.INFINITE_SCROLL and mode != ViewMode.INFINITE_SCROLL:
            self.infinite_scroll_view.calculate_current_index()

        if mode == ViewMode.SIDE_BY_SIDE and self.view_mode == ViewMode.SIDE_BY_SIDE:
            self.side_count = 3 if self.side_count == 2 else 2
            self.btn_mode_sbs.setText(f"⧉ {self.side_count}")
            self.side_by_side_view.update_viewers()
            self.side_by_side_view.update_images()
            QTimer.singleShot(50, self.reset_zoom)
            self.save_settings()
            return

        self.view_mode = mode
        self.stacked_widget.setCurrentIndex(int(mode))
        self.btn_mode_sbs.setText(f"⧉ {self.side_count}")
        self.save_settings()
        
        is_scroll = (mode == ViewMode.INFINITE_SCROLL)
        if mode == ViewMode.SIDE_BY_SIDE:
            QTimer.singleShot(50, self.reset_zoom)
        self.btn_prev.setVisible(not is_scroll)
        self.btn_next.setVisible(not is_scroll)
        self.btn_reset_zoom.setVisible(not is_scroll)
        
        self.update_image()
        
        if is_scroll:
            self.infinite_scroll_view.update_view(jump_to_current=True)
        elif mode == ViewMode.SIDE_BY_SIDE:
            self.side_by_side_view.update_viewers()
            self.side_by_side_view.update_images()

    def on_zoom_slider_changed(self, value):
        self.apply_zoom(value / 100.0)
        label_text = f"{value}%"
        self.lbl_zoom.setText(label_text)
        
        if hasattr(self, 'zoom_lbl_ss'):
            self.zoom_lbl_ss.setText(label_text)
        
        if hasattr(self, 'zoom_slider'):
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(value)
            self.zoom_slider.blockSignals(False)
            
        if hasattr(self, 'zoom_slider_ss'):
            self.zoom_slider_ss.blockSignals(True)
            self.zoom_slider_ss.setValue(value)
            self.zoom_slider_ss.blockSignals(False)
            
        if self.view_mode == ViewMode.INFINITE_SCROLL:
            self.infinite_scroll_view.update_view()

    def apply_zoom(self, relative_zoom):
        if self.view_mode == ViewMode.STANDARD:
            self.standard_view.set_zoom(relative_zoom)
        elif self.view_mode == ViewMode.SIDE_BY_SIDE:
            for viewer in self.side_by_side_view.viewers:
                viewer.set_zoom(relative_zoom)

    def update_zoom_ui(self, relative_zoom):
        val = int(relative_zoom * 100)
        self.lbl_zoom.setText(f"{val}%")
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(val)
        self.zoom_slider.blockSignals(False)
        
    def save_data_now(self):
        data = {'filenames': self.filenames, 'current_index': self.current_index}
        self.logic_manager.save_data(data if self.reopen_images_bool else {})
            
    def add_path(self, filenames=None, clear=False):
        if clear:
            self.logic_manager.save_paths([])
            self.paths = []
        else:
            if not filenames: return
            new_paths = [p for p in self.paths if p.get('path') != filenames]
            new_paths.append({'path': filenames, 'timestamp': time.time()})
            self.paths = sorted(new_paths, key=lambda x: x.get('timestamp', 0), reverse=True)[:MAX_RECENT_PATHS]
            self.logic_manager.save_paths(self.paths)
            self.update_recents_visibility()

    def save_paths_data(self):
        self.logic_manager.save_paths(self.paths)
                
    def refresh_paths(self):
        self.recent_menu.clear()
        for i, entry in enumerate(self.paths):
            if i == MAX_RECENT_PATHS: break
            path_list = entry.get('path', [])
            if not path_list: continue
            short_lbl = f"{i+1}: {str(path_list[0])[:100]}..."
            action = QAction(short_lbl, self)
            action.triggered.connect(partial(self.read_im, path_list))
            self.recent_menu.addAction(action)
        self.update_recents_visibility()

    def update_recents_visibility(self):
        should_show = self.save_paths or len(self.paths) > 0
        self.btn_recents.setVisible(should_show)

    def select_images(self):
        extensions = self.logic_manager.get_supported_extensions()
        ext_filter = " ".join([f"*{ext}" for ext in extensions])
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select images", "", f"Image Files ({ext_filter});;All Files (*.*)")
        if files:
            self.load_files(files)
            
    def apply_sorting(self):
        if not self.original_filenames: return
        if self.sort_mode == 'name':
            self.filenames = sorted(self.original_filenames)
        elif self.sort_mode == 'date':
            try:
                self.filenames = sorted(self.original_filenames, key=os.path.getmtime, reverse=False)
            except Exception:
                self.filenames = sorted(self.original_filenames)

    def toggle_sort(self):
        self.sort_mode = 'date' if self.sort_mode == 'name' else 'name'
        self.apply_sorting()
        if hasattr(self, 'btn_sort'):
            self.btn_sort.setText(f"⇅ {self.sort_mode.capitalize()}")
        if self.filenames:
            self.read_im(self.filenames, 0)
                
    def read_im(self, files, index=0):
        self.filenames = files
        self.images_len = len(self.filenames)
        self.logic_manager.clear_cache()
        if self.images_len > 0:
            self.current_index = index if index < self.images_len else 0
            self.save_settings()
            self.update_image()

    def get_pixmap(self, index):
        return self.logic_manager.get_pixmap(self.filenames, index)

    def get_exif(self, index):
        return self.logic_manager.get_exif(self.filenames, index)
            
    def update_image(self):
        if not self.filenames: return
        if self.view_mode == ViewMode.STANDARD:
            pixmap = self.get_pixmap(self.current_index)
            if not pixmap.isNull():
                self.image_viewer.set_image(pixmap)
                if not self.save_zoom or not hasattr(self, '_zoomed_once'):
                    if self.image_viewer.width() > 10:
                        self.image_viewer.fit_image()
                        self._zoomed_once = True
        elif self.view_mode == ViewMode.SIDE_BY_SIDE:
            self.side_by_side_view.update_images()
        elif self.view_mode == ViewMode.INFINITE_SCROLL:
            self.infinite_scroll_view.update_view()
        self.update_label()
        
    def reset_zoom(self):
        if self.view_mode == ViewMode.STANDARD:
            self.standard_view.fit_image()
        elif self.view_mode == ViewMode.SIDE_BY_SIDE:
            for viewer in self.side_by_side_view.viewers:
                viewer.fit_image()
        self.update_zoom_ui(1.0)
        
    def update_zoom_label(self, f):
        self.lbl_zoom.setText(f"{int(f * 100)}%")

    def update_label(self):
        self.lbl_index.setText(f"{self.current_index + 1}/{self.images_len}")
        if self.show_label and self.filenames:
            full_fname = os.path.basename(self.filenames[self.current_index])
            metrics = self.name_label.fontMetrics()
            elided_fname = metrics.elidedText(full_fname, Qt.TextElideMode.ElideMiddle, 300)
            self.name_label.setText(elided_fname)
            self.name_label.setToolTip(full_fname)
            self.name_label.show()
        else:
            self.name_label.hide()
            
    def prev_image(self, shift=None):
        if self.images_len == 0: return
        if isinstance(shift, bool): shift = None
        if self.internal_ss_active:
            self.last_ss_advance_time = time.time()
        if self.view_mode == ViewMode.INFINITE_SCROLL:
            self.infinite_scroll_view.scroll_prev()
            return
        if shift is None:
            shift = self.side_count if self.view_mode == ViewMode.SIDE_BY_SIDE else 1
        self.current_index = (self.current_index - shift) % self.images_len
        self.update_image()
        self.reset_zoom()
        
    def next_image(self, shift=None):
        if self.images_len == 0: return
        if isinstance(shift, bool): shift = None
        if self.internal_ss_active:
            self.last_ss_advance_time = time.time()
        if self.view_mode == ViewMode.INFINITE_SCROLL:
            self.infinite_scroll_view.scroll_next()
            return
        if shift is None:
            shift = self.side_count if self.view_mode == ViewMode.SIDE_BY_SIDE else 1
        self.current_index = (self.current_index + shift) % self.images_len
        self.update_image()
        self.reset_zoom()

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        
    def open_help(self):
        QDesktopServices.openUrl(QUrl("https://github.com/Vxwilson/picturexviewer"))
        
    def open_recents_dialog(self):
        dlg = RecentPathsDialog(self)
        dlg.exec()
        
    def open_slideshow_initiator(self):
        if not self.filenames: return
        dlg = SlideshowInitiator(self)
        dlg.exec()

    def toggle_internal_slideshow(self):
        if not self.filenames: return
        self.internal_ss_active = not self.internal_ss_active
        if self.internal_ss_active:
            self.internal_ss_paused = False
            self.last_ss_advance_time = time.time()
            self.internal_ss_timer.start(500)
            self.btn_toggle_ss.setText("⏸")
            self.set_ss_zen_mode(True)
        else:
            self.internal_ss_timer.stop()
            self.btn_toggle_ss.setText("▶")
            self.set_ss_zen_mode(False)

    def update_ss_clock(self):
        if not self.internal_ss_active or self.internal_ss_paused:
            if self.internal_ss_paused:
                self.ss_status_overlay.setText(f"Paused ({self.slide_show_time})")
                self.ss_status_overlay.adjustSize()
                self._reposition_overlay()
            return

        elapsed = time.time() - self.last_ss_advance_time
        remaining = self.slide_show_time - elapsed
        if remaining <= 0:
            self.next_image()
            self.last_ss_advance_time = time.time()
            remaining = self.slide_show_time
        self.ss_status_overlay.setText(f"{int(remaining)}s ({self.slide_show_time})")
        self.ss_status_overlay.adjustSize()
        self._reposition_overlay()

    def set_ss_zen_mode(self, enabled):
        self.menuBar().setVisible(not enabled)
        self.bottom_frame.setVisible(not enabled)
        self.name_label.setVisible(not enabled and self.show_label)
        if enabled:
            self.ss_status_overlay.show()
            self.zoom_overlay.show()
            self.ss_status_overlay.raise_()
            self.zoom_overlay.raise_()
            self._reposition_overlay()
        else:
            self.ss_status_overlay.hide()
            self.zoom_overlay.hide()

    def _reposition_overlay(self):
        x = (self.width() - self.ss_status_overlay.width()) // 2
        self.ss_status_overlay.move(x, 20)
        self.zoom_overlay.adjustSize()
        x_ss = (self.width() - self.zoom_overlay.width()) // 2
        self.zoom_overlay.move(x_ss, self.height() - 70)

    def keyPressEvent(self, event):
        if self.internal_ss_active:
            if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_T):
                self.internal_ss_paused = not self.internal_ss_paused
                self.last_ss_advance_time = time.time()
                self.update_ss_clock() 
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.toggle_internal_slideshow()
                return
            elif event.key() == Qt.Key.Key_Up:
                self.slide_show_time += 1
                self.save_settings()
                self.update_ss_clock()
                return
            elif event.key() == Qt.Key.Key_Down:
                if self.slide_show_time > 1:
                    self.slide_show_time -= 1
                    self.save_settings()
                    self.update_ss_clock()
                return
            elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_J):
                shift = 1 if (event.modifiers() & Qt.KeyboardModifier.ControlModifier or event.key() == Qt.Key.Key_J) else None
                self.prev_image(shift)
                return
            elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_L):
                shift = 1 if (event.modifiers() & Qt.KeyboardModifier.ControlModifier or event.key() == Qt.Key.Key_L) else None
                self.next_image(shift)
                return
        super().keyPressEvent(event)
        
    def open_fs_slideshow(self):
        self._pre_slideshow_geometry = self.saveGeometry()
        self.hide()
        self.ss_win = SlideshowWindow(self)
