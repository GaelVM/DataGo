import json
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://pokemongo.com"
NEWS_URL = f"{BASE_URL}/es/news"
OUTPUT_FILE = "temp/noticias.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubActionBot/1.0)"
}


def normalize_spaces(text: str) -> str:
    return " ".join((text or "").split()).strip()


def fetch_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def extract_json_ld_news(soup: BeautifulSoup) -> list[dict]:
    """
    Extrae noticias desde el JSON-LD tipo ItemList.
    Es la fuente más estable porque no depende de clases CSS.
    """
    news = []

    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        blocks = data if isinstance(data, list) else [data]

        for block in blocks:
            if not isinstance(block, dict):
                continue

            if block.get("@type") != "ItemList":
                continue

            for item in block.get("itemListElement", []):
                if not isinstance(item, dict):
                    continue

                title = normalize_spaces(item.get("name", ""))
                link = item.get("url", "")

                if not title or not link:
                    continue

                news.append({
                    "title": title,
                    "date": "",
                    "image": "",
                    "link": urljoin(BASE_URL, link)
                })

    return news


def enrich_news_from_cards(soup: BeautifulSoup, news_list: list[dict]) -> list[dict]:
    """
    Completa fecha e imagen recorriendo las cards visibles.
    Hace match por link.
    """
    by_link = {item["link"]: item for item in news_list}

    for card in soup.select('a[href^="/es/news/"], a[href^="/es/post/"]'):
        href = card.get("href", "")
        if not href:
            continue

        link = urljoin(BASE_URL, href)
        item = by_link.get(link)
        if not item:
            continue

        date_tag = card.select_one("pg-date-format")
        if date_tag:
            item["date"] = normalize_spaces(date_tag.get_text(" ", strip=True))

        img_tag = card.select_one("img")
        if img_tag and img_tag.has_attr("src"):
            item["image"] = img_tag["src"]

    return list(by_link.values())


def extract_news_from_cards_only(soup: BeautifulSoup) -> list[dict]:
    """
    Fallback si el JSON-LD falla.
    Evita depender de una clase específica para el título.
    """
    news_list = []

    for card in soup.select('a[href^="/es/news/"], a[href^="/es/post/"]'):
        href = card.get("href", "")
        if not href:
            continue

        link = urljoin(BASE_URL, href)

        date_tag = card.select_one("pg-date-format")
        date = normalize_spaces(date_tag.get_text(" ", strip=True)) if date_tag else ""

        img_tag = card.select_one("img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        # Buscar título sin depender de una clase compilada concreta
        title = ""
        divs = card.find_all("div")
        texts = [normalize_spaces(div.get_text(" ", strip=True)) for div in divs]
        texts = [t for t in texts if t]

        # Tomamos el último texto no vacío como heurística:
        # normalmente el orden es fecha -> título
        if texts:
            title = texts[-1]

        # Si por algún motivo el último coincide con la fecha, buscamos otro
        if title and title == date and len(texts) > 1:
            for candidate in reversed(texts[:-1]):
                if candidate != date:
                    title = candidate
                    break

        if not title:
            continue

        news_list.append({
            "title": title,
            "date": date,
            "image": image,
            "link": link
        })

    return news_list


def deduplicate_news(news_list: list[dict]) -> list[dict]:
    seen = set()
    result = []

    for item in news_list:
        link = item.get("link", "")
        if not link or link in seen:
            continue
        seen.add(link)
        result.append(item)

    return result


def scrape_latest_news() -> list[dict]:
    soup = fetch_soup(NEWS_URL)

    # 1) Intento principal: JSON-LD
    news_list = extract_json_ld_news(soup)

    if news_list:
        news_list = enrich_news_from_cards(soup, news_list)
        return deduplicate_news(news_list)

    # 2) Fallback: parseo directo de cards
    news_list = extract_news_from_cards_only(soup)
    return deduplicate_news(news_list)


def save_to_json(data: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    latest_news = scrape_latest_news()
    save_to_json(latest_news, OUTPUT_FILE)
    print(f"{len(latest_news)} noticias guardadas en '{OUTPUT_FILE}'")