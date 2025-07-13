import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://pokemongo.com"
NEWS_URL = f"{BASE_URL}/es_mx/news"
OUTPUT_FILE = "temp/noticias.json"

def scrape_latest_news():
    response = requests.get(NEWS_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    news_list = []

    for post in soup.select(".blogList__post"):
        link = BASE_URL + post.get("href", "")
        img_tag = post.select_one("img.image")
        image = img_tag["src"] if img_tag else ""

        date_tag = post.select_one(".blogList__post__content__date")
        date = date_tag.get_text(strip=True) if date_tag else ""

        title_tag = post.select_one(".blogList__post__content__title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        news_list.append({
            "title": title,
            "date": date,
            "image": image,
            "link": link
        })

    return news_list

def save_to_json(data, path):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    latest_news = scrape_latest_news()
    save_to_json(latest_news, OUTPUT_FILE)
    print(f"{len(latest_news)} noticias guardadas en '{OUTPUT_FILE}'")
