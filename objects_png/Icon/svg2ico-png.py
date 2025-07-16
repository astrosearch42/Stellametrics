import cloudconvert
import os

API_KEY = "" # Remplacez par votre clé API CloudConvert format string
# Vous pouvez obtenir une clé API en vous inscrivant sur https://cloudconvert.com
if not API_KEY:
    raise ValueError("Veuillez fournir une clé API CloudConvert.")


cloudconvert.configure(api_key=API_KEY)

folder = os.path.join("objects_png", "Icon")
svg_files = [f for f in os.listdir(folder) if f.lower().endswith(".svg")]
if not svg_files:
    print("Aucun fichier SVG trouvé dans le dossier.")
    exit(1)
print("Fichiers SVG disponibles :")
for i, f in enumerate(svg_files):
    print(f"{i+1}. {f}")
choice = input("Entrez le numéro ou le nom du fichier SVG à convertir en ICO : ").strip()
if choice.isdigit():
    idx = int(choice) - 1
    if idx < 0 or idx >= len(svg_files):
        print("Numéro invalide.")
        exit(1)
    filename = svg_files[idx]
else:
    if choice not in svg_files:
        print("Nom de fichier invalide.")
        exit(1)
    filename = choice
svg_path = os.path.join(folder, filename)
ico_path = os.path.splitext(svg_path)[0] + ".ico"
if os.path.exists(ico_path):
    print(f"Le fichier ICO existe déjà : {ico_path}")
    action = input("Voulez-vous le remplacer ? (o/n) : ").strip().lower()
    if action != "o":
        print("Conversion annulée.")
        exit(0)
import tempfile
print(f"Conversion de {svg_path} en PNG temporaire...")
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
print(f"PNG temporaire créé : {png_path}")

# 2. PNG -> ICO
print(f"Conversion du PNG temporaire en ICO...")
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
print(f"Fichier ICO téléchargé : {ico_path}")

# 3. Supprime le PNG temporaire
print(f"Conversion terminée. Fichiers générés :\n- SVG : {svg_path}\n- PNG : {png_path}\n- ICO : {ico_path}")