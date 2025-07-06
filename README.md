# SkyScale

A PyQt5 application to visualize and compare astronomical images (FITS, PNG, JPG, etc.), measure distances, and add reference objects.

## Features
- Visualization of FITS and standard images
- Segment measurement and real distance calculation
- Add reference objects (France, USA, Earth, Jupiter, ...)
- Save and load presets
- Generate a Windows executable
- Convert SVG to ICO automatically with the provided script and personal CloudConvert's API 

## Icon Conversion (SVG to ICO)
If you want to use your own icon for the application:

1. Convert your SVG to ICO using an online tool (e.g. https://cloudconvert.com/svg-to-ico).
2. Place the ICO file in `objects_png/Icon/`.
3. Use the provided script to convert all SVG files in that folder to ICO:
   ```powershell
   python objects_png/Icon/svg2ico.py
   ```
   
> Note: Direct SVG to ICO conversion in Python without external dependencies or internet is not possible. Use a personal API key in CloudConvert.com or convert SVG to PNG to ICO (at the end you must have a `icon.ico` in the `objects_png/Icon/` folder).

## Installation 
In a bash/cmd shell:
1. Enter in your working folder:
   `cd <working directory path>`
1. Create a python environment in that folder:
   `python -m venv <env name>`
2. Activate environment and enter it:
   `<env name>/Scripts/activate`
   `cd <env name>`
2. Clone the repository:
   `git clone https://github.com/astrosearch42/SkyScale`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Run the application:
   `python SkyScale.py`


## Building the Executable
To create a standalone Windows executable (.exe) for SkyScale, follow these steps:
1. Make sure all dependencies are installed in your environment:
   `pip install -r requirements.txt`
2. Install PyInstaller if not already installed:
   `pip install pyinstaller`
3. In your project folder, run the following command (PowerShell or cmd), it might take a while:
   ```powershell
   pyinstaller --onefile --windowed \
     --add-data "objects_png;objects_png" \
     --add-data "Main/ImageViewer.ui;Main" \
     --add-data "Library/distance_library.json;Library" \
     --add-data "Library/de421.bsp;Library" \
     --add-data "preset;preset" \
     Main/SkyScale.py
   ```
   - `--onefile` creates a single .exe file
   - `--windowed` prevents a console window from opening
   - `--add-data` includes required files and folders (use `;` as separator on Windows)

   If you encounter issues with the multi-line command above, use the following single-line version instead:

   ```powershell
   pyinstaller --onefile --windowed --add-data "objects_png;objects_png" --add-data "Main/ImageViewer.ui;Main" --add-data "Library/distance_library.json;Library" --add-data "Library/de421.bsp;Library" --add-data "preset;preset" Main/SkyScale.py
   ```

4. The executable will be created in the `dist` folder as `SkyScale.exe`.

5. (Optional) Create a shortcut to the executable:
   - Open the `dist` folder where `SkyScale.exe` is located.
   - Right-click on `SkyScale.exe` and select "Create shortcut".
   - Move the shortcut to your Desktop or any convenient location for quick access.

6. Double-click `dist/SkyScale.exe` (or your shortcut) to launch the application.

## Author
- Pseudo : astrosearch42 
- GitHub : https://github.com/astrosearch42
