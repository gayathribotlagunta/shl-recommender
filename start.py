import os
import json

# Generate catalog on startup if not present
if not os.path.exists("catalog.json"):
    print("Generating catalog...")
    from scraper import get_known_catalog
    catalog = get_known_catalog()
    with open("catalog.json", "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"Catalog generated: {len(catalog)} assessments")

# Start the app
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8000)