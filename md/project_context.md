# Project Context for AI Coding

This document serves as a guide for AI agents working on PictureXViewer.

## Guidelines

1. Do not automatically bump version number or update versionhistory.md unless explicitly asked. When asked to bump, if not explicitly asked to bump to a specific version, bump to the next depending on the update content:
    - If it is a bug fix or small refactor/feature, bump to the next patch version (e.g. 0.3.0 -> 0.3.1).
    - If it is a new and significant feature, bump to the next minor version (e.g. 0.3.0 -> 0.4.0).
    - Never bump to the next major version as it is not the versioning scheme for this project.

2. **Modular Integrity**: Maintain the separation of concerns between `src/core` (logic) and `src/ui` (visuals).

## Architecture (v0.7.2+)

PictureXViewer is built with **PyQt6** and follows a modular package structure.

### Project Structure
- **`src/`**: All source code.
  - **`core/`**: Non-UI logic (Data persistence, image engine).
  - **`ui/`**: UI components (Main Window, Slideshow, Dialogs).
  - **`utils/`**: Shared constants and helper functions.
- **`data/`**: Runtime state and user settings.
- **`assets/`**: Icons and design elements.
- **`main.py`**: Clean application entry point.

### Core Components
- **LogicManager (`src/core/logic_manager.py`)**: Centralized engine for settings, history, and image metadata caching.
- **MainWindow (`src/ui/main_window.py`)**: Orchestrates the multi-view environment.
- **QImageViewer (`src/ui/widgets.py`)**: High-performance rendering engine using `QGraphicsView` for hardware acceleration.
- **RecentPathsDialog (`src/ui/dialogs.py`)**: Advanced session manager with preview capabilities and search.

## Performance and Scaling (Critical)

### macOS High-DPI
On macOS, fractional scaling can cause windows to "snap" to maximized states incorrectly.
- **Scaling Policy**: We use `setHighDpiScaleFactorRoundingPolicy(PassThrough)` in `main.py`.
- **Window Restoration**: `SlideshowWindow.closeEvent` restores geometry from `MainWindow._pre_slideshow_geometry`.

---

## Progress and Milestones

- [x] Implement Multi-Mode Viewer (Standard, Side-By-Side, Infinite Scroll).
- [x] Add Folder Drag-and-Drop support.
- [x] **Modular Codebase Refactor** (v0.7.2).
- [ ] Transition from `pickle` to `JSON` for settings management (Next).
- [ ] Add support for GIF playback.
- [ ] Implement advanced image filtering (size, aspect ratio).
