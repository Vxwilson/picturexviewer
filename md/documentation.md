# PictureXViewer User and Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation and Requirements](#installation-and-requirements)
3. [User Guide](#user-guide)
   - [Opening Images](#opening-images)
   - [Viewing Modes](#viewing-modes)
   - [Recent Sessions](#recent-sessions)
4. [Keyboard Shortcuts](#keyboard-shortcuts)
   - [Main Window Shortcuts](#main-window-shortcuts)
   - [Slideshow Window Shortcuts](#slideshow-window-shortcuts)
5. [Technical Architecture](#technical-architecture)
   - [Modular Structure](#modular-structure)
   - [High-DPI Scaling](#high-dpi-scaling)
   - [Data Persistence](#data-persistence)

---

## Overview
PictureXViewer is a simple image viewing application. It offers multiple viewing modes, including side-by-side comparisons and an infinite scroll feed, as well as a robust slideshow system.

## Installation and Requirements (Manual Build)
### System Requirements
- Operating System: macOS, Windows, or Linux.
- Python Version: Python 3.9 or higher.

### Dependencies
- PyQt6: Used for the graphical user interface.
- Pillow (PIL): Used for image metadata (EXIF) processing.
- screeninfo: Used for multi-monitor detection in slideshow mode.

### Setup Instructions
1. Install the required libraries:
   ```bash
   pip3 install PyQt6 Pillow screeninfo
   ```
2. Run the application from the root directory:
   ```bash
   python3 main.py
   ```

---

## User Guide

### Opening Images
Users can import images into the viewer using several methods:
- **File Dialog**: Accessible via File > Read from file, or by pressing `O`.
- **Drag and Drop**: Folders or individual image files can be dropped directly onto the application window.
- **Auto-Sort**: When enabled in settings, images are automatically sorted by filename or modification date upon loading.

### Viewing Modes
The application features three distinct viewing modes:
1. **Standard View**: Displays a single image at a time. Supports high-performance panning and zooming.
2. **Side-by-Side View**: Displays two or three images simultaneously. This mode is useful for comparison. Pressing the Side-by-Side button multiple times toggles between 2 and 3 columns.
3. **Infinite Scroll**: Displays images in a vertical, scrollable batch feed. This mode uses lazy loading to maintain performance with large datasets.

### Recent Sessions
The Recent Sessions dialog (`Ctrl + R` or the clock icon) allows users to:
- Browse history of previously opened batches.
- Preview images within a session before loading it.
- Search sessions by directory path or filename.
- Filter out entries where the local files have been moved or deleted.

---

## Keyboard Shortcuts

`Cmd` is used on macOS, `Ctrl` is used on Windows and Linux.

### Main Window Shortcuts
| Key | Action |
| --- | --- |
| `O` / `Ctrl+O` | Open file dialog |
| `1` | Switch to Standard View |
| `2` | Switch to Side-by-Side View |
| `3` | Switch to Infinite Scroll View |
| `Right` / `>` | Next image(s) |
| `Left` / `<` | Previous image(s) |
| `L` | Next image (single step in side-by-side) |
| `J` | Previous image (single step in side-by-side) |
| `S` | Start Fullscreen Slideshow |
| `Alt+Shift+S` | Toggle Internal Slideshow (Zen Mode) |
| `Ctrl + E` | Show EXIF Metadata |
| `Alt+S` / `Ctrl+S` | Toggle Sort Mode (Name/Date) |
| `Alt + P` | Open Preferences |
| `Ctrl + Wheel` | Zoom In / Out |
| `0` | Reset Zoom to 100% |
| `Up` | Increase Slideshow Timer (When Active) |
| `Down` | Decrease Slideshow Timer (When Active) |

### Slideshow Window Shortcuts
| Key | Action |
| --- | --- |
| `Space` / `T` | Pause / Resume Slideshow |
| `Right` / `Wheel Down` | Advance to next image(s) |
| `Left` / `Wheel Up` | Return to previous image(s) |
| `Ctrl + Right` / `L` | Advance by 1 image |
| `Ctrl + Left` / `J` | Return by 1 image |
| `Up` | Increase Timer interval |
| `Down` | Decrease Timer interval |
| `1` - `9` | Move Slideshow to specified Monitor |
| `Esc` / `Right Click` | Exit Slideshow |

---

## Technical Architecture

### Modular Structure
The application is organized into the following package structure:
- **`src/`**: Parent package for all source code.
  - **`core/`**: Contains the `LogicManager` which handles non-UI tasks such as data persistence, EXIF parsing, and image scanning logic.
  - **`ui/`**: Contains all UI-related modules.
    - **`windows`**: Top-level windows (`MainWindow`, `SlideshowWindow`).
    - **`dialogs`**: Modal windows for settings, metadata, and history.
    - **`widgets`**: Custom subclasses of Qt widgets used across the app.
  - **`utils/`**: General helper functions and constants.

### High-DPI Scaling
To ensure visual fidelity on Retina and 4K displays, the application uses hardware-accelerated rendering through `QGraphicsView`. A specific scaling policy (`PassThrough`) is applied at the application entry point to prevent blurry rendering or incorrect window snapping on macOS.

### Data Persistence
User settings and session data are stored in the `data/` directory using the Python `pickle` module:
- `settings.txt`: Application preferences.
- `paths.txt`: Session history data.
- `save.txt`: State of the last opened session for auto-reloading.
