import cloudconvert
import os

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZDgyMDI5NWU2NDIxMjk1ZmNmNWIyYjkwYTQxZTBkNGRkZjNhNDQwYWE0YTg3NGI1YjI0MmM2YWUxYjJiM2IwZDgyZThmNGQ2ZmVhYjkxZGEiLCJpYXQiOjE3NTE4NDE4OTAuMDA1NDY3LCJuYmYiOjE3NTE4NDE4OTAuMDA1NDY5LCJleHAiOjQ5MDc1MTU0ODkuOTk5MjYyLCJzdWIiOiI3MjM3MzY5NSIsInNjb3BlcyI6WyJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIl19.e2Gb_p3ieT0AhWZNYMuIW_ktRdB2jDDuf96iP1FCEySSX5v_UYqK6M2lanJ5cr4-HZClgMu9cRozaHAF7mbak_02m-Ld7Waoe0fC2iJTgBw3QzVSw8nS_RR-7TRs2IEntm_SSNrDrV6T8Tyygj56immYerlE3QI9a-8bPD9x9mSSYxcPXKk6RBlFPPQfFoT6mc6TosOaH_vE1AYC-b367jbUtGENkiYuYd19ziL3_hS1Xer9Pnwy1f_rJvvvHW7-sjCU-A7yq0cpmI4RMjOW3OKi8WNaxKxvET21XG4lXXmj79u5d1Z2W5HqAsO8gUCUYyqDPIaVQvdmSvCjsbmZ_R2sy9JLaYpvdkC-opjk60rzQiDcO2iH6KicpuoBnzfJ-5PgdJUxsjd0i7gq6D7w7XSTHbq2N2nijuc57PPMrodOO5MasKD7_BM9B7MUl1Fh9k2iw2mn-E4mGoMcGvptk7PpznJUc0hVfAUJJCpaday7wDipZWvkhy6u6jthidn9C6NJXqCqYbi1v21Mtdq_r522FX6Dvj6Eh8niCTxNwQRtJx9PegtTMZsFzdyYwplBQ2V2qYwfZ0J-jwI2R0DzMw7QkehvuPlO7ToP2YRHfyxD-bzku3fvpMqWtZegDXacXWR-VhevS7DW_hnrasCJPTa4Mik2mLR3Lgj_SuVnLpE"

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