import platform
from enum import IntEnum
import os

# Versioning
def get_version_from_history():
    """Extracts the latest version (e.g., v0.3.0) from versionhistory.md."""
    try:
        # Move up one level since this file will be in src/
        v_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "md", "versionhistory.md")
        if os.path.exists(v_path):
            with open(v_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("## v"):
                        return line.split(" ")[1].strip()
    except Exception:
        pass
    return "v0.7.2"  # Fallback

CURRENT_VERSION_RAW = get_version_from_history()
CURRENT_VERSION = f"PictureXViewer {CURRENT_VERSION_RAW} (PyQt6)"
CURRENT_OS = platform.system()

class ViewMode(IntEnum):
    STANDARD = 0
    SIDE_BY_SIDE = 1
    INFINITE_SCROLL = 2

# Configuration
DEFAULT_SIDE_COUNT = 2
DEFAULT_SLIDE_SHOW_TIME = 3
DEFAULT_SCREEN_DIS = 1
MAX_RECENT_PATHS = 15
PIXMAP_CACHE_SIZE = 10
BATCH_SIZE = 30
