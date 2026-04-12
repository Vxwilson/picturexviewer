## v0.7.2 (2026-04-12)

- **Architectural Overhaul**: Transitioned from a monolithic `main.py` to a modular package structure under `src/`.
- **UI/Logic Separation**: Decoupled visual components from core data management and persistence.
- **Improved Maintainability**: Extracted CSS styles into a dedicated module and centralized application constants.
- **Fixed Zoom Logic**: Restored the requirement for the `Control`/`Command` modifier for mouse wheel zooming.
- **Shortcut Restoration**: Re-enabled missing keyboard shortcuts for view mode switching (`1`, `2`, `3`) and zoom reset (`0`).
- **Reliability Fixes**: Resolved refactor-related bugs including missing imports in dialog modules and clean entry point handling.
- **Data Organization**: Migrated runtime settings and caches to a dedicated `data/` directory.

## v0.7.1
- **Robust Drag-and-Drop Loader**:
    - **Hidden File Filtering**: Automatically skips macOS metadata files (`._`) and other hidden system files (like `.DS_Store`) during folder drops to prevent loading broken images.
    - **Guaranteed WebP Support**: Explicitly ensures `.webp` and other modern formats are included in the folder scanner, even if not natively reported by the Qt environment.
    - **Smarter Path Normalization**: Improved recursive scanning to skip hidden directories (e.g., `.git`, `.venv`) for faster and cleaner loading.

## v0.7.0
- **Modern Footer UI Overhaul**:
    - **True Pill-Style Buttons**: All footer controls now feature a fully rounded `12px` radius for a premium, contemporary aesthetic.
    - **Emoji-Driven Navigation**: Replaced text-heavy labels with intuitive emoji icons (📁 Open, 🕒 Recents, ⇅ Sort, ◀/▶ Navigation, ⟲ Reset) for a cleaner layout.
    - **Integrated Mode Control**: The view-mode toggles (Standard, Side-by-Side, Scroll) are now unified into a single pill-shaped segmented control.
    - **Sleek Zoom Slider**: Ported the refined slideshow slider design to the main application footer.
- **Contextual UX Improvements**:
    - **Smart Filename Display**: Filenames in the footer now use middle-eliding to fit perfectly within the bar while remaining readable.
    - **Enhanced History Context**: The "Open Recent" dialog now prioritizes immediate parent folder names, making it easier to identify sessions at a glance.

## v0.6.0
- **Drag-and-Drop Folder Support**:
    - **Instant Directory Loading**: You can now drag any folder (or multiple folders) from Finder directly onto the application to load all images instantly.
    - **Full-Window Coverage**: The entire viewer area (Standard, Side-by-Side, and Infinite Scroll) now accepts drops, not just the footer.
    - **Automatic Session History**: Dropped folders are automatically recorded in "Recent Sessions" with their full contents.
    - **Refactored File Pipeline**: Unified the opening logic to ensure consistent sorting and history management across all methods of loading images.

## v0.5.4
- **Final Stability Boost**:
    - **Session Load Perfection**: Increased the startup delay to 400ms and added a secondary "Double-Force Fit" command 100ms after the initial load.
    - Resolves the "hidden image" issue when relaunching from varied UI states (like internal slideshow).

## v0.5.3
- **Stability Enhancements**:
    - **Final Launch Visibility Fix**: Postponed initial image loading to ensure the OS has finalized layout geometry, resolving the "no image on launch" race condition.
    - **Smarter Zoom Fitting**: The app now verifies child viewer integrity before marking an image as "fitted".
- **UX Improvements**:
    - **Interactive Zoom Icon**: The magnifying glass in Zen mode is now a clickable button to instantly reset zoom to 100%.

## v0.5.2
- **Zen Mode Enhancements**:
    - Added a **Floating Zoom Slider** specifically for internal slideshow mode.
    - Premium, translucent overlay that provides visual feedback and direct control over zoom while in immersive view.
    - Seamlessly synchronized with mouse wheel zoom and standard footer controls.

## v0.5.1
- **Bug Fixes**:
    - **Initial Launch Visibility**: Fixed an issue where the image would not show on first launch.
    - **Navigation Navigation**: Fixed broken "Next/Prev" buttons and arrow key shortcuts (was caused by signal arguments).
    - **Responsive Zoom**: Implemented automatic **Reset Zoom** on window resize for all modes.
    - **SlideShow Controls**: Improved reliability of Up/Down keys for timer adjustment in internal slideshow mode.

## v0.5.0
- **Multi-Mode Viewer Integration**:
    - Replaced the single-image central widget with a `StackedWidget` supporting three distinct viewing experiences.
    - **Standard Mode (1)**: Classic single-image view with full zoom/pan.
    - **Side-by-Side Mode (2)**: Dynamic horizontal layout for 2 or 3 images (toggleable).
    - **Seamless Infinite Scroll (3)**: Gallery view with **automatic lazy loading** and high-performance `QImageReader` decoding.
- **Enhanced Footer Controls**:
    - Added stylized **Mode Icons** (⧠, ⧉, ☰) for quick switching.
    - Integrated a **Universal Zoom Slider** (10% - 500%) across all viewing modes.
    - Implemented **Automatic Zoom Reset** when switching layouts for a clean "fitted" start.
- **Recent Sessions Overhaul**:
    - Replaced manual pagination (Prev/Next buttons) with **Infinite Scroll** in the preview panel.
    - Implemented a **"Hybrid Seed"** loading system: loads the first image instantly for selection speed, then seeds additional images to prime the scroll mechanism.
    - Added a **Live Progress Status** indicator to track loaded images within each session history.
- **Persistence & QoL**:
    - App now remembers and restores the last used `ViewMode` on startup.
    - Improved keyboard shortcuts (1, 2, 3) for instant mode switching.
    - Set default Side-by-Side count to 2 for better out-of-the-box experience.

## v0.4.1
- **High-Performance Batched Preview**: 
    - Replaced the static single preview with a **scrollable thumbnail list**.
    - Implemented a **30-image batching system** to ensure performance on large sessions.
    - Added **Pagination Controls** (← Prev / Next →) to navigate batches within the preview pane.
    - Thumbnails now automatically scale to fill the width of the preview pane for maximum clarity.
- **Improved Dialog Quality-of-Life**:
    - Added a **Live Search Bar** to filter recent sessions by path or filename.
    - Implemented a **Context Menu** for session rows (Reveal in Finder/Explorer, Remove from History).
    - Added a **"Clear History"** button at the bottom of the dialog with a safety confirmation prompt.
    - Added a premium **dark mode scrollbar** for a more refined appearance.

## v0.4.0

## v0.3.0
- **PyQt6 Migration**: Fully migrated the application from Tkinter to PyQt6/PySide6 for better High-DPI (Retina/4K) support and hardware-accelerated rendering.
- **Mac OS Optimizations**: Implemented `PassThrough` scaling policy for consistent window management on macOS.
- **Slideshow Fixes**:
    - Resolved "fitting" issues where images wouldn't zoom correctly on the first load.
    - Added robust window restoration to prevent the main window from unintentionally maximizing after exiting a slideshow.
- **Improved UI**: Switched to `QGraphicsView` architecture for logically perfect pixel rendering.

## v0.2.7
- Sorting mode now correctly switches between date and name.
- Shift-by-one now works on macOS via alternative keys (`J`/`L`).

## v0.2.6
- Added support for `.webp` images.

## v0.2.5
- Added paused indicator in slideshow mode.
- Added feature to move +1/-1 image in slideshow mode, instead of just going to next/previous.

## v0.2.3.2
- Added mouse controls for slideshow, opening images, and in-slideshow mode.

## v0.2.2
- Upsized images when in 3-image slideshow mode.
- Added auto-sort images from selection (with enable/disable option).

## v0.2.1
- Fixed monitor positioning issue; slideshows now consistently work on the correct target monitors.
