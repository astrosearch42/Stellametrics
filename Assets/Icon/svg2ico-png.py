import cloudconvert
import os

API_KEY = "" # Replace with your CloudConvert API key (string)
# You can get an API key by signing up at https://cloudconvert.com
if not API_KEY:
    raise ValueError("Please provide a CloudConvert API key.")

cloudconvert.configure(api_key=API_KEY)

folder = os.path.join("objects_png", "Icon")
svg_files = [f for f in os.listdir(folder) if f.lower().endswith(".svg")]
if not svg_files:
    print("No SVG files found in the folder.")
    exit(1)
print("Available SVG files:")
for i, f in enumerate(svg_files):
    print(f"{i+1}. {f}")
choice = input("Enter the number or name of the SVG file to convert to ICO: ").strip()
if choice.isdigit():
    idx = int(choice) - 1
    if idx < 0 or idx >= len(svg_files):
        print("Invalid number.")
        exit(1)
    filename = svg_files[idx]
else:
    if choice not in svg_files:
        print("Invalid file name.")
        exit(1)
    filename = choice
svg_path = os.path.join(folder, filename)
ico_path = os.path.splitext(svg_path)[0] + ".ico"
if os.path.exists(ico_path):
    print(f"ICO file already exists: {ico_path}")
    action = input("Do you want to overwrite it? (y/n): ").strip().lower()
    if action != "y":
        print("Conversion cancelled.")
        exit(0)
import tempfile
print(f"Converting {svg_path} to temporary PNG...")
# 1. SVG -> PNG
png_path = os.path.splitext(svg_path)[0] + ".png"
job_svg2png = cloudconvert.Job.create(payload={
    "tasks": {
        "import-1": {
            "operation": "import/upload"
        },
        "convert-1": {
            "operation": "convert",
            "input": "import-1",
            "input_format": "svg",
            "output_format": "png",
            "engine": "inkscape"
        },
        "export-1": {
            "operation": "export/url",
            "input": "convert-1"
        }
    }
})
upload_task = job_svg2png["tasks"][0]
cloudconvert.Task.upload(svg_path, upload_task)
job_svg2png = cloudconvert.Job.wait(id=job_svg2png["id"])
export_task = [t for t in job_svg2png["tasks"] if t["name"] == "export-1"][0]
file_url = export_task["result"]["files"][0]["url"]
import requests
r = requests.get(file_url)
with open(png_path, "wb") as f:
    f.write(r.content)
print(f"PNG created: {png_path}")

# 2. PNG -> ICO
print(f"Converting PNG to ICO...")
job_png2ico = cloudconvert.Job.create(payload={
    "tasks": {
        "import-1": {
            "operation": "import/upload"
        },
        "convert-1": {
            "operation": "convert",
            "input": "import-1",
            "input_format": "png",
            "output_format": "ico"
        },
        "export-1": {
            "operation": "export/url",
            "input": "convert-1"
        }
    }
})
upload_task = job_png2ico["tasks"][0]
cloudconvert.Task.upload(png_path, upload_task)
job_png2ico = cloudconvert.Job.wait(id=job_png2ico["id"])
export_task = [t for t in job_png2ico["tasks"] if t["name"] == "export-1"][0]
file_url = export_task["result"]["files"][0]["url"]
r = requests.get(file_url)
with open(ico_path, "wb") as f:
    f.write(r.content)
print(f"ICO file downloaded: {ico_path}")

# 3. Print summary
print(f"Conversion complete. Files generated:\n- SVG: {svg_path}\n- PNG: {png_path}\n- ICO: {ico_path}")