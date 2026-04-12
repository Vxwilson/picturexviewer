# PictureXViewer

PictureXViewer is a simple image viewer and side-by-side slideshow tool built with **Python 3** and **PyQt6**. It supports modern high-resolution displays.

## Key Features

- **Multi-Mode Viewing**:
  - **Standard View**: Fast, high-quality individual image viewing.
  - **Side-by-Side**: Compare 2 or 3 images simultaneously.
  - **Infinite Scroll**: Browse entire folders in a smooth, hardware-accelerated scrollable feed.
- **Customizable Slideshow**: Timer-based image rotation with support for multi-monitor setups.
- **Recent Sessions**: Manage and search your history with rich thumbnail previews.
- **EXIF Viewer**: Quickly inspect image metadata.

## Run it Manually

### Setup
```bash
pip3 install PyQt6 Pillow screeninfo
```

### Quick Start

Run the application from the root directory:
```bash
python3 main.py
```

## Documentation

For a comprehensive guide on all features, view modes, and a full list of keyboard shortcuts, please refer to the [Detailed Documentation](md/documentation.md).

## Project Structure

- `src/`: Core application logic and UI modules.
- `data/`: Local user settings and session history.
- `assets/`: Static icons and design assets.
- `main.py`: Clean entry point.

## Contributing

The codebase is optimized for maintainability and AI-assisted development. Please refer to [project_context.md](project_context.md) for technical guidelines.
