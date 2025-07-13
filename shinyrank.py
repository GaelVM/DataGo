import os
import json
from fractions import Fraction
import requests

url = "https://shinyrates.com/data/rate/"

# Realizar la solicitud HTTP para obtener los datos JSON
response = requests.get(url)

# Verifica si la solicitud fue exitosa (código de estado 200)
if response.status_code == 200:
    data = response.json()

    # Iterar sobre cada elemento y agregar la clave "img"
    for pokemon in data:
        pokemon["img"] = f"https://raw.githubusercontent.com/GaelVM/DBImages/main/PokemonGo/Pokemon/Img/{pokemon['id']}.png"

    # Función auxiliar para convertir la cadena en un número manejando comas y fracciones
    def parse_rate(rate):
        try:
            # Intentar convertir como número flotante
            return float(rate.replace(',', ''))
        except ValueError:
            try:
                # Si falla, intentar convertir como fracción eliminando comas
                return float(Fraction(rate.replace(',', '')))
            except ValueError:
                # Si aún falla, lanzar una excepción
                raise ValueError(f'No se pudo convertir {rate} a número o fracción válida')

    # Crear el rango personalizado y agregar la clave "rank"
    for index, pokemon in enumerate(sorted(data, key=lambda x: 1/parse_rate(x["rate"]))):
        pokemon["rank"] = index + 1

    # Define la carpeta temporal
    temp_folder = "temp"

    # Verifica si la carpeta temporal ya existe, y si no, créala
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Define la ruta completa del archivo JSON en la carpeta temporal
    json_file_path = os.path.join(temp_folder, "rankshiny.json")

    # Guardar el diccionario en un archivo JSON en la carpeta temporal
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)

    print(f"Datos guardados en {json_file_path}")

else:
    print(f"Error al obtener la página. Código de estado: {response.status_code}")
