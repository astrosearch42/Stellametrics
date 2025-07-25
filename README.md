


# Stellametrics

Stellametrics is a cross-platform PyQt5 application for visualizing, measuring, and comparing astronomical images (FITS, PNG, JPG, etc.). It allows you to measure distances, overlay reference objects, and manage instrument presets.

## Features
- View FITS and standard image formats
- Draw segments and calculate real distances
- Overlay reference objects (Earth, Jupiter, France, USA, etc.)
- Save/load instrument presets
- Customizable themes
- Windows/macOS/Linux support (Python 3.8+)
- Build a standalone executable (Windows)
- Batch convert SVG to ICO/PNG for app icons (CloudConvert API supported)

## Installation

### 1. Quick & Easy Installation with the Executable

The fastest and easiest way to use Stellametrics is to download the pre-built executable:

1. Download the file `!Executable/Stellametrics.exe`.
   - You can also download the folder itself to get images to test the app
2. Place `Stellametrics.exe` wherever you want (Desktop, Documents, external drive, etc.).
3. Double-click `Stellametrics.exe` to launch the application. No need to install Python or any dependencies.
4. (Optional) Create a shortcut for quick access: right-click on `Stellametrics.exe` → "Create shortcut" → move the shortcut to your Desktop.

**NB:** When you first open `Stellametrics.exe`, Windows may display a security warning (SmartScreen) saying that the publisher is unknown. This is normal for unsigned applications. You can safely click on "More info" and then "Run anyway" to launch the application. Stellametrics does not contain any malware or unwanted software. You can check by yourself in the main code.

**This method is highly recommended for users who want a fast and hassle-free setup.**

### 2. Installation with Git Clone

---
Linux prerequisites:
If you are on Linux, you may need to install some system packages first:
```bash
sudo apt install python3.11-venv git binutils
```

- `python3.11-venv`  : provides the Python 3.11 virtual environment module (for creating isolated Python environments)
- `git`  : version control system used to clone and manage the repository
- `binutils`  : a set of binary tools required by some Python packages during installation
---


1. Create and activate a Python virtual environment (Recommended):
   ```bash
   cd <your-folder>   # (enter in the folder where you want to install the project)
   python -m venv Stellametrics.env
   # On Windows:
   Stellametrics.env\Scripts\activate
   # On macOS/Linux:
   source Stellametrics.env/bin/activate
   ```
   **To deactivate the virtual environment just write ```deactivate```**
2. Once activated, clone the repository in the environment:
   ```bash
   cd Stellametrics.env
   git clone https://github.com/astrosearch42/Stellametrics
   cd Stellametrics
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python Main/Stellametrics.py
   ```

## Building a Standalone Executable (Windows)
1. Install PyInstaller (in the virtual environment):
   ```bash
   pip install pyinstaller
   ```
2. In the project root, run:
   ```powershell
   pyinstaller --onefile --windowed --icon "Assets/Icon/icon.ico" \
     --add-data "Assets;Assets" \
     --add-data "Main/ImageViewer.ui;Main" \
     --add-data "Main/StyleSheets;Main/StyleSheets" \
     --add-data "Library/distance_library.json;Library" \
     --add-data "Library/de421.bsp;Library" \
     --add-data "Library/fonts;Library/fonts" \
     --add-data "Preset;Preset" \
     --add-data "Stellametrics_Config;Stellametrics_Config" \
     --strip \
     Main/Stellametrics.py
   ```
   - On Windows, use `;` as the separator in `--add-data`. On macOS/Linux, use `:` instead.
   - If you encounter issues with the multi-line command, use a single line (see PyInstaller docs) or run this line :
   1. Windows:
   ```powershell
   pyinstaller --onefile --windowed --icon "Assets/Icon/icon.ico" --add-data "Assets;Assets" --add-data "Main/ImageViewer.ui;Main" --add-data "Main/StyleSheets;Main/StyleSheets" --add-data "Library/distance_library.json;Library" --add-data "Library/de421.bsp;Library" --add-data "Library/fonts;Library/fonts" --add-data "Preset;Preset" --add-data "Stellametrics_Config;Stellametrics_Config" --strip Main/Stellametrics.py
   ```
   2. macOS/Linux:
   ```powershell
   pyinstaller --onefile --windowed --icon "Assets/Icon/icon.ico" --add-data "Assets:Assets" --add-data "Main/ImageViewer.ui:Main" --add-data "Main/StyleSheets:Main/StyleSheets" --add-data "Library/distance_library.json:Library" --add-data "Library/de421.bsp:Library" --add-data "Library/fonts:Library/fonts" --add-data "Preset:Preset" --add-data "Stellametrics_Config:Stellametrics_Config" --strip Main/Stellametrics.py
   ```

3. The executable will be created in the `dist` folder as `Stellametrics.exe`.

## Usage
- Launch the app with `python Main/Stellametrics.py` or by opening the executable.
- To create a desktop shortcut (Windows):
  1. Open the `dist` folder where `Stellametrics.exe` is located.
  2. Right-click on `Stellametrics.exe` and select "Create shortcut".
  3. Move the shortcut to your Desktop or any convenient location for quick access.
- **Note:** You can move the `Stellametrics.exe` file anywhere you want (e.g., Desktop, Documents, external drive, etc.). The application is fully portable as long as all required files are included during packaging.
- Open images, draw segments, add reference objects, and save your presets.
  (Images are provided in the folder `Assets/Examples/` to test by yourself.)
- For advanced usage and troubleshooting, see the code comments and issues on GitHub.

## Icon Conversion (SVG to ICO/PNG)
To use a custom icon:
1. Place your SVG file(s) in `Assests/Icon/`.
2. Use the provided script to convert all SVGs to ICO and PNG:
   ```bash
   python objects_png/Icon/svg2ico-png.py
   ```
   - Requires a CloudConvert API key (see script for details), and so a limited usage (10 conversions a day).
   - Alternatively, use any online converter (e.g. https://cloudconvert.com/svg-to-ico) and place the resulting `icon.ico` in `Assets/Icon/`.


## Uninstallation

#### 1. Uninstall the Executable (Windows)
To uninstall Stellametrics if you used the pre-built executable, simply delete the file `Stellametrics.exe` (and its shortcut if you created one). No other steps are required.

#### 2. Remove the Python Environment (Source Install)
If you installed from source and created a virtual environment, you can remove it by deleting the environment folder. For example:

```bash
rm -rf ./Stellametrics.env # Outside the folder
```
This will completely remove the isolated Python environment and all installed dependencies. If you only want to remove the cloned source code, simply delete the `Stellametrics` folder.

## Author
- GitHub: [Maxime Bertrand](https://github.com/astrosearch42)
