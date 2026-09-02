import argparse
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from app.core.constants import LAWS_TO_SCRAPE

OUTPUT_DIR = Path("lex_structured")
LOG_FILE = Path("logs/scraper.log")
REQUEST_TIMEOUT = 30
REQUEST_DELAY_SECONDS = 2
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
ARTICLE_PATTERNS = (
    re.compile(r"(\d+)-modda", re.IGNORECASE),
    re.compile(r"modda\s+(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)-статья", re.IGNORECASE),
    re.compile(r"статья\s+(\d+)", re.IGNORECASE),
)


def configure_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
        force=True,
    )


logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_article_number(text: str) -> Optional[str]:
    for pattern in ARTICLE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_document(session: requests.Session, url: str) -> BeautifulSoup:
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def parse_articles(content_root: BeautifulSoup, doc_name: str) -> dict[str, dict]:
    elements = content_root.find_all(["p", "h1", "h2", "h3", "h4", "div", "span"])
    if not elements:
        full_text = clean_text(content_root.get_text(" ", strip=True))
        return {"1": {"title": doc_name, "content": full_text}} if full_text else {}

    articles: dict[str, dict] = {}
    current_article_num: Optional[str] = None
    current_title = doc_name
    current_content: list[str] = []

    for element in elements:
        text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue

        article_num = extract_article_number(text)
        if article_num:
            if current_article_num and current_content:
                articles[current_article_num] = {
                    "title": current_title,
                    "content": "\n".join(current_content),
                }
            current_article_num = article_num
            current_title = text
            current_content = []
            continue

        current_content.append(text)

    if current_article_num and current_content:
        articles[current_article_num] = {
            "title": current_title,
            "content": "\n".join(current_content),
        }
    elif current_content:
        articles["1"] = {
            "title": doc_name,
            "content": "\n".join(current_content),
        }

    return articles


def scrape_law_document(url: str, doc_name: str) -> dict[str, dict]:
    logger.info("scrape start | document=%s | url=%s", doc_name, url)
    session = build_session()
    try:
        soup = fetch_document(session, url)
        content_root = soup.find(id="divBody")
        if content_root is None:
            logger.warning("scrape skipped | document=%s | reason=divBody not found", doc_name)
            return {}

        articles = parse_articles(content_root, doc_name)
        logger.info("scrape done | document=%s | sections=%d", doc_name, len(articles))
        return articles
    except requests.RequestException:
        logger.exception("scrape failed | document=%s | stage=request", doc_name)
        return {}
    except Exception:
        logger.exception("scrape failed | document=%s | stage=parse", doc_name)
        return {}
    finally:
        session.close()


def save_to_json(data: dict, filename: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    logger.info("write done | file=%s", output_path)


def scrape_all_laws() -> None:
    total = len(LAWS_TO_SCRAPE)
    success_count = 0

    for index, (doc_name, url) in enumerate(LAWS_TO_SCRAPE.items(), start=1):
        logger.info("batch progress | current=%d | total=%d | document=%s", index, total, doc_name)
        articles = scrape_law_document(url, doc_name)
        if articles:
            save_to_json(articles, f"{doc_name}.json")
            success_count += 1
        if index < total:
            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("batch done | success=%d | total=%d", success_count, total)


def update_single_law(doc_name: str) -> None:
    url = LAWS_TO_SCRAPE.get(doc_name)
    if url is None:
        valid_names = ", ".join(sorted(LAWS_TO_SCRAPE))
        raise ValueError(f"Unknown law: {doc_name}. Available: {valid_names}")

    articles = scrape_law_document(url, doc_name)
    if articles:
        save_to_json(articles, f"{doc_name}.json")


def list_scraped_laws() -> None:
    if not OUTPUT_DIR.exists():
        logger.info("no scraped laws found")
        return

    files = sorted(OUTPUT_DIR.glob("*.json"))
    if not files:
        logger.info("no scraped laws found")
        return

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        size_kb = path.stat().st_size / 1024
        logger.info(
            "scraped law | name=%s | articles=%d | size_kb=%.1f",
            path.stem,
            len(data),
            size_kb,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scraper.py")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("doc_name")

    return parser


def main() -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        list_scraped_laws()
        return
    if args.command == "update":
        update_single_law(args.doc_name)
        return
    scrape_all_laws()


if __name__ == "__main__":
    main()
