import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://pokemongo.com"
NEWS_URL = f"{BASE_URL}/es/news"
OUTPUT_FILE = "temp/noticias.json"

def scrape_latest_news():
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []

    for card in soup.select('a[href^="/es/news/"], a[href^="/es/post/"]'):
        link = BASE_URL + card.get("href", "")
        
        # Título de la noticia
        title_tag = card.select_one("div._size\\:heading_1vw4u_16")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Fecha
        date_tag = card.select_one("pg-date-format")
        date = date_tag.get_text(strip=True) if date_tag else ""
        
        # Imagen
        img_tag = card.select_one("img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        news_list.append({
            "title": title,
            "date": date,
            "image": image,
            "link": link
        })

    return news_list

def save_to_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    latest_news = scrape_latest_news()
    save_to_json(latest_news, OUTPUT_FILE)
    print(f"{len(latest_news)} noticias guardadas en '{OUTPUT_FILE}'")
