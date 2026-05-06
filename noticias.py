import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://pokemongo.com"
NEWS_URL = f"{BASE_URL}/es/news"
OUTPUT_FILE = Path("temp/noticias.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PokemonGoNewsScraper/2.0)"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


@dataclass
class NewsItem:
    title: str
    date: str
    image: str
    link: str


def normalize_spaces(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def fetch_soup(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"No se pudo descargar la página: {url}") from exc

    return BeautifulSoup(response.text, "html.parser")


def iter_json_ld_blocks(soup: BeautifulSoup) -> Iterable[dict[str, Any]]:
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logging.warning("Se ignoró un bloque JSON-LD inválido.")
            continue

        if isinstance(data, list):
            for block in data:
                if isinstance(block, dict):
                    yield block
        elif isinstance(data, dict):
            yield data


def extract_json_ld_news(soup: BeautifulSoup) -> list[NewsItem]:
    items: list[NewsItem] = []

    for block in iter_json_ld_blocks(soup):
        if block.get("@type") != "ItemList":
            continue

        for entry in block.get("itemListElement", []):
            if not isinstance(entry, dict):
                continue

            title = normalize_spaces(entry.get("name"))
            link = normalize_spaces(entry.get("url"))

            if not title or not link:
                continue

            items.append(
                NewsItem(
                    title=title,
                    date="",
                    image="",
                    link=urljoin(BASE_URL, link),
                )
            )

    return items


def parse_timestamp_date(tag) -> str:
    timestamp = tag.get("timestamp") if tag else None

    if timestamp and str(timestamp).isdigit():
        seconds = int(timestamp) / 1000
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()

    return normalize_spaces(tag.get_text(" ", strip=True)) if tag else ""


def best_image_from_card(card) -> str:
    img = card.select_one("img[src]")
    if img:
        return normalize_spaces(img.get("src"))

    source = card.select_one("source[srcset]")
    if source:
        srcset = normalize_spaces(source.get("srcset"))
        first = srcset.split(",")[0].strip()
        return first.split(" ")[0].strip()

    return ""


def title_from_card(card, fallback: str = "") -> str:
    # En el HTML actual, el título suele estar en el último div del contenido.
    content = card.select_one('[class*="newsCardContent"]')
    scope = content or card

    candidates = [
        normalize_spaces(div.get_text(" ", strip=True))
        for div in scope.find_all("div")
    ]
    candidates = [text for text in candidates if text]

    date_tag = card.select_one("pg-date-format")
    date_text = normalize_spaces(date_tag.get_text(" ", strip=True)) if date_tag else ""

    for text in reversed(candidates):
        if text and text != date_text:
            return text

    return fallback


def extract_cards(soup: BeautifulSoup) -> dict[str, NewsItem]:
    cards: dict[str, NewsItem] = {}

    for card in soup.select('a[href^="/es/news/"], a[href^="/es/post/"]'):
        href = normalize_spaces(card.get("href"))
        if not href:
            continue

        link = urljoin(BASE_URL, href)
        date_tag = card.select_one("pg-date-format")
        date = parse_timestamp_date(date_tag)
        image = best_image_from_card(card)
        title = title_from_card(card)

        if not title:
            continue

        cards[link] = NewsItem(
            title=title,
            date=date,
            image=image,
            link=link,
        )

    return cards


def merge_news(json_ld_items: list[NewsItem], card_items: dict[str, NewsItem]) -> list[NewsItem]:
    merged: dict[str, NewsItem] = {}

    for item in json_ld_items:
        card = card_items.get(item.link)

        merged[item.link] = NewsItem(
            title=card.title if card and card.title else item.title,
            date=card.date if card else item.date,
            image=card.image if card else item.image,
            link=item.link,
        )

    # Si JSON-LD no trae todo, añadimos tarjetas restantes.
    for link, item in card_items.items():
        merged.setdefault(link, item)

    return list(merged.values())


def scrape_latest_news() -> list[NewsItem]:
    soup = fetch_soup(NEWS_URL)

    json_ld_news = extract_json_ld_news(soup)
    card_news = extract_cards(soup)

    news = merge_news(json_ld_news, card_news)

    logging.info("Noticias encontradas: %s", len(news))
    return news


def save_to_json(data: list[NewsItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = [asdict(item) for item in data]

    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    latest_news = scrape_latest_news()
    save_to_json(latest_news, OUTPUT_FILE)
    print(f"{len(latest_news)} noticias guardadas en '{OUTPUT_FILE}'")


if __name__ == "__main__":
    main()