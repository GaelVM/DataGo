import os
import requests
from bs4 import BeautifulSoup
import json

temp_folder = "temp"
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

url = "https://pokemongolive.com/news/?hl=es"

# Añadir headers con User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
html = response.text
soup = BeautifulSoup(html, "html.parser")

# Buscar el contenedor de entradas
blog_posts_div = soup.find("div", class_="blogList__posts")

if not blog_posts_div:
    raise Exception("⚠️ No se encontró el div 'blogList__posts'. Puede que el contenido sea dinámico o la estructura haya cambiado.")

post_links = blog_posts_div.find_all("a", class_="blogList__post")

posts_data = []
for post_link in post_links:
    post_url = "https://pokemongolive.com" + post_link["href"]
    post_image = post_link.find("img")["src"]
    post_date = post_link.find("div", class_="blogList__post__content__date").text.strip()
    post_title = post_link.find("div", class_="blogList__post__content__title").text.strip()

    posts_data.append({
        "URL": post_url,
        "Image": post_image,
        "Date": post_date,
        "Title": post_title
    })

json_file_path = os.path.join(temp_folder, "noticias.json")
with open(json_file_path, "w", encoding="utf-8") as json_file:
    json.dump(posts_data, json_file, ensure_ascii=False, indent=2)

print(f"✅ Datos guardados en {json_file_path}")
