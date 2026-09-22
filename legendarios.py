import json
import requests
import os
import re

url = "https://raw.githubusercontent.com/GaelVM/DataDuck/data/events.json"

response = requests.get(url)
response.raise_for_status()

original_json = response.json()

filtered_raid_events = [
    event for event in original_json
    if event.get("eventType") == "raid-hour"
]

new_json = []

for event in filtered_raid_events:

    pokemon_names = event.get("name", "").replace(" Raid Hour", "").strip()

    # Convierte:
    # "Xurkitree, Pheromosa, and Buzzwole"
    # en:
    # ["Xurkitree", "Pheromosa", "Buzzwole"]
    pokemon_list = re.split(r",\s*|\s+and\s+", pokemon_names)

    for pokemon_name in pokemon_list:

        pokemon_name = pokemon_name.strip()

        if not pokemon_name:
            continue

        fm_value = None
        formatted_name = pokemon_name

        # Manejo de Forme
        if " Forme " in pokemon_name:
            parts = pokemon_name.split(" Forme ", 1)

            if len(parts) == 2:
                fm_value = parts[0].strip()
                formatted_name = f"{parts[1].strip()} {parts[0].strip()}"

        new_event = {
            "name": formatted_name,
            "start": event.get("start"),
            "end": event.get("end"),
            "extraData": event.get("extraData", {})
        }

        if fm_value:
            new_event["fm"] = fm_value

        new_json.append(new_event)

temp_folder = "temp"

os.makedirs(temp_folder, exist_ok=True)

json_file_path = os.path.join(temp_folder, "raid_hour.json")

with open(json_file_path, "w", encoding="utf-8") as file:
    json.dump(
        new_json,
        file,
        indent=4,
        ensure_ascii=False
    )

print("Nuevo JSON creado con éxito.")