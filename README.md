# SkyScale

SkyScale is a cross-platform PyQt5 application for visualizing, measuring, and comparing astronomical images (FITS, PNG, JPG, etc.). It allows you to measure distances, overlay reference objects, and manage instrument presets.

## Features
- View FITS and standard image formats
- Draw segments and calculate real distances
- Overlay reference objects (Earth, Jupiter, France, USA, etc.)
- Save/load instrument presets
- Customizable themes
- Windows/macOS/Linux support (Python 3.8+)
- Build a standalone executable (Windows)
- Batch convert SVG to ICO/PNG for app icons (CloudConvert API supported)

## Icon Conversion (SVG to ICO/PNG)
To use a custom icon:
1. Place your SVG file(s) in `objects_png/Icon/`.
2. Use the provided script to convert all SVGs to ICO and PNG:
   ```bash
   python objects_png/Icon/svg2ico-png.py
   ```
   - Requires a CloudConvert API key (see script for details), and so a limited usage (10 conversions a day).
   - Alternatively, use any online converter (e.g. https://cloudconvert.com/svg-to-ico) and place the resulting `icon.ico` in `objects_png/Icon/`.

## Installation
**Linux prerequisites:**
If you are on Linux, you may need to install some system packages first:
```bash
sudo apt install python3.11-venv git binutils
```

1. Clone the repository:
   ```bash
   git clone https://github.com/astrosearch42/SkyScale
   cd SkyScale
   ```
2. (Recommended) Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python Main/SkyScale.py
   ```

## Building a Standalone Executable (Windows)
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. In the project root, run:
   ```powershell
   pyinstaller --onefile --windowed --icon "objects_png/Icon/icon.ico" \
     --add-data "objects_png;objects_png" \
     --add-data "Main/ImageViewer.ui;Main" \
     --add-data "Main/StyleSheets;Main/StyleSheets" \
     --add-data "Library/distance_library.json;Library" \
     --add-data "Library/de421.bsp;Library" \
     --add-data "Library/fonts;Library/fonts" \
     --add-data "Preset;Preset" \
     Main/SkyScale.py
   ```
   - On Windows, use `;` as the separator in `--add-data`. On macOS/Linux, use `:` instead.
   - If you encounter issues with the multi-line command, use a single line (see PyInstaller docs) or run this line :
   1. Windows:
   ```powershell
   pyinstaller --onefile --windowed --icon "objects_png/Icon/icon.ico" --add-data "objects_png;objects_png" --add-data "Main/ImageViewer.ui;Main" --add-data "Main/StyleSheets;Main/StyleSheets" --add-data "Library/distance_library.json;Library" --add-data "Library/de421.bsp;Library" --add-data "Library/fonts;Library/fonts" --add-data "Preset;Preset" Main/SkyScale.py
   ```
   2. macOS/Linux:
   ```powershell
   pyinstaller --onefile --windowed --icon "objects_png/Icon/icon.ico" --add-data "objects_png:objects_png" --add-data "Main/ImageViewer.ui:Main" --add-data "Main/StyleSheets:Main/StyleSheets" --add-data "Library/distance_library.json:Library" --add-data "Library/de421.bsp:Library" --add-data "Library/fonts:Library/fonts" --add-data "Preset:Preset" Main/SkyScale.py
   ```

3. The executable will be created in the `dist` folder as `SkyScale.exe`.

## Usage
- Launch the app with `python Main/SkyScale.py` or by double-clicking the executable (Windows).
- To create a desktop shortcut (Windows):
  1. Open the `dist` folder where `SkyScale.exe` is located.
  2. Right-click on `SkyScale.exe` and select "Create shortcut".
  3. Move the shortcut to your Desktop or any convenient location for quick access.
- Open images, draw segments, add reference objects, and save your presets.
- For advanced usage and troubleshooting, see the code comments and issues on GitHub.

## Author
- GitHub: [Maxime Bertrand](https://github.com/astrosearch42)
