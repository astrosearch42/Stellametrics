import cloudconvert
import os

API_KEY = "" # Remplacez par votre clé API CloudConvert format string
# Vous pouvez obtenir une clé API en vous inscrivant sur https://cloudconvert.com
if not API_KEY:
    raise ValueError("Veuillez fournir une clé API CloudConvert.")


cloudconvert.configure(api_key=API_KEY)

folder = os.path.join("objects_png", "Icon")
for filename in os.listdir(folder):
    if filename.lower().endswith(".svg"):
        svg_path = os.path.join(folder, filename)
        ico_path = os.path.splitext(svg_path)[0] + ".ico"
        print(f"Conversion de {svg_path} en {ico_path} ...")
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-1": {
                    "operation": "import/upload"
                },
                "convert-1": {
                    "operation": "convert",
                    "input": "import-1",
                    "input_format": "svg",
                    "output_format": "ico"
                },
                "export-1": {
                    "operation": "export/url",
                    "input": "convert-1"
                }
            }
        })
        upload_task = job["tasks"][0]
        upload_url = upload_task["result"]["form"]["url"]
        cloudconvert.Task.upload(svg_path, upload_task)
        job = cloudconvert.Job.wait(id=job["id"])
        export_task = [t for t in job["tasks"] if t["name"] == "export-1"][0]
        file_url = export_task["result"]["files"][0]["url"]
        # Téléchargement du fichier ICO
        import requests
        r = requests.get(file_url)
        with open(ico_path, "wb") as f:
            f.write(r.content)
        print(f"Fichier téléchargé : {ico_path}")

print("Conversion terminée pour tous les fichiers SVG du dossier.")