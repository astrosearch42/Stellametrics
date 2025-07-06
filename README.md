# AstroScale

A PyQt5 application to visualize and compare astronomical images (FITS, PNG, JPG, etc.), measure distances, and add reference objects.

## Features
- Visualization of FITS and standard images
- Segment measurement and real distance calculation
- Add reference objects (France, USA, Earth, Jupiter, ...)
- Save and load presets
- Generate a Windows executable

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
   `git clone https://github.com/astrosearch42/AstroScale`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Run the application:
   `python AstroScale.py`

## Building the Executable
To create a standalone Windows executable (.exe) for AstroScale, follow these steps:
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
     Main/AstroScale.py
   ```
   - `--onefile` creates a single .exe file
   - `--windowed` prevents a console window from opening
   - `--add-data` includes required files and folders (use `;` as separator on Windows)

   If you encounter issues with the multi-line command above, use the following single-line version instead:

   ```powershell
   pyinstaller --onefile --windowed --add-data "objects_png;objects_png" --add-data "Main/ImageViewer.ui;Main" --add-data "Library/distance_library.json;Library" --add-data "Library/de421.bsp;Library" Main/AstroScale.py
   ```

4. The executable will be created in the `dist` folder as `AstroScale.exe`.

5. (Optional) Create a shortcut to the executable:
   - Open the `dist` folder where `AstroScale.exe` is located.
   - Right-click on `AstroScale.exe` and select "Create shortcut".
   - Move the shortcut to your Desktop or any convenient location for quick access.

6. Double-click `dist/AstroScale.exe` (or your shortcut) to launch the application.

## Author
- Pseudo : astrosearch42 
- GitHub : https://github.com/astrosearch42
