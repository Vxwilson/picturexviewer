# Stylesheet constants for PictureXViewer

MAIN_WINDOW_STYLE = """
    QMainWindow { background-color: #2B2D30; }
"""

COMMON_BUTTON_STYLE = """
    QPushButton { 
        background-color: #3B3E43; 
        color: #CCC; 
        border: 1px solid #4F5258; 
        border-radius: 12px; 
        padding: 2px 12px; 
        font-size: 11px; 
        font-weight: bold; 
        min-height: 24px;
    }
    QPushButton:hover { 
        background-color: #4B4E53; 
        color: white; 
        border-color: #5F6268;
    }
    QPushButton:pressed { 
        background-color: #3574F0; 
        border-color: #4B85F2; 
        color: white;
    }
"""

FOOTER_FRAME_STYLE = """
    QFrame { 
        background-color: #212224; 
        border-top: 1px solid #3F4344;
    }
    """ + COMMON_BUTTON_STYLE + """
    QLabel { color: #81878B; font-size: 11px; }
    
    QSlider { background: transparent; border: none; }
    QSlider::groove:horizontal { 
        background: #18191B; 
        height: 4px; 
        border-radius: 2px; 
    }
    QSlider::handle:horizontal { 
        background: #788BA0; 
        width: 14px; 
        height: 14px; 
        margin: -5px 0; 
        border-radius: 7px; 
    }
    QSlider::handle:horizontal:hover { 
        background: #8A9CB2; 
    }
"""

ZEN_ZOOM_OVERLAY_STYLE = """
    background-color: rgba(0,0,0,120); border-radius: 12px; border: none;
"""

ZEN_ZOOM_ICON_STYLE = """
    color: #AAA; background: transparent; border: none; font-size: 14px;
"""

ZEN_SLIDER_STYLE = """
    QSlider { background: transparent; border: none; }
    QSlider::groove:horizontal { background: #333; height: 4px; border-radius: 2px; }
    QSlider::handle:horizontal { background: #788BA0; width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; }
    QSlider::handle:horizontal:hover { background: #8A9CB2; }
"""

RECENTS_DIALOG_STYLE = """
    QDialog { background-color: #2B2D30; color: #EEE; }
    QListWidget { background-color: #1E1F22; border: 1px solid #3F4344; border-radius: 6px; outline: none; }
    QListWidget::item { border-bottom: 1px solid #333; padding: 2px; }
    QListWidget::item:selected { background-color: #3574F0; border-radius: 4px; }
    QListWidget::item:hover { background-color: #2D2F33; border-radius: 4px; }
    
    QLineEdit { background-color: #1E1F22; border: 1px solid #3F4344; border-radius: 4px; padding: 6px; color: #EEE; }
    
    QPushButton { background-color: #3574F0; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold; min-width: 80px; }
    QPushButton:hover { background-color: #4B85F2; }
    QPushButton#batchBtn { background-color: #3B3E43; color: #BBB; border: 1px solid #4F5258; padding: 4px 8px; font-size: 11px; }
    QPushButton#batchBtn:hover { background-color: #4B4E53; color: white; }
    QPushButton#dangerBtn { background-color: #442222; }
    QPushButton#dangerBtn:hover { background-color: #662222; }
    
    QFrame#previewFrame { background-color: #1E1F22; border: 1px solid #3F4344; border-radius: 6px; }
    QCheckBox { color: #BBB; }
    
    QScrollArea { border: none; background-color: transparent; }
    QScrollBar:vertical {
        border: none;
        background: #1E1F22;
        width: 8px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #3F4344;
        min-height: 20px;
        border-radius: 4px;
    }
    QScrollBar::handle:vertical:hover {
        background: #4F5354;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

OVERLAY_LABEL_STYLE = """
    color: white; font-size: 16px; background-color: rgba(0,0,0,180); padding: 5px; border-radius: 5px;
"""

ZEN_STATUS_OVERLAY_STYLE = """
    color: white; font-size: 16px; background-color: rgba(0,0,0,180); padding: 8px 15px; border-radius: 8px;
"""

SLIDESHOW_BG_STYLE = "background-color: #3B3D3F;"

SCROLL_AREA_STYLE = "background-color: #1E1F22; border: none;"

CONTEXT_MENU_STYLE = """
    QMenu { background-color: #2B2D30; color: #EEE; border: 1px solid #3F4344; } 
    QMenu::item:selected { background-color: #3574F0; }
"""
