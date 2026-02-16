#!/usr/bin/env python3
"""
verify_links.py — data/articles.json의 모든 링크를 검증하고,
죽은 링크(404, "존재하지 않는 기사" 등)를 제거합니다.
"""

import json
import os
import re
import sys

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# 기사 페이지에서 "죽은 페이지"를 감지하기 위한 키워드 목록
DEAD_PAGE_KEYWORDS = [
    "페이지를 찾을 수 없습니다",
    "존재하지 않는 페이지",
    "존재하지 않는 기사",
    "삭제된 기사",
    "요청하신 페이지를",
    "찾을 수 없",
    "기사가 없습니다",
    "기사를 찾을 수",
    "해당 기사가 존재하지",
    "유효하지 않은 기사",
    "404 not found",
    "page not found",
    "invalid article",
    "이 기사는 더 이상",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def is_dead_page(url: str) -> tuple[bool, str]:
    """URL이 죽은 페이지인지 확인합니다.

    Returns:
        (is_dead: bool, reason: str)
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
    except requests.RequestException as e:
        return True, f"CONNECTION_ERROR: {e}"

    if resp.status_code >= 400:
        return True, f"HTTP_{resp.status_code}"

    body_lower = resp.text.lower()
    for keyword in DEAD_PAGE_KEYWORDS:
        if keyword.lower() in body_lower:
            return True, f"DEAD_TEXT: '{keyword}'"

    return False, "OK"


def verify(articles_path: str) -> dict:
    """articles.json을 읽어서 링크를 검증하고, 살아있는 것만 남깁니다."""
    with open(articles_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_before = 0
    total_after = 0

    for cat in data.get("categories", []):
        verified = []
        for article in cat.get("articles", []):
            total_before += 1
            url = article["url"]
            dead, reason = is_dead_page(url)
            if dead:
                print(f"  ✗ DEAD ({reason}) → {url}")
            else:
                print(f"  ✓ OK → {url}")
                verified.append(article)
                total_after += 1
        cat["articles"] = verified

    print(f"\n검증 결과: {total_before}건 중 {total_after}건 살아있음 ({total_before - total_after}건 제거)")
    return data


def main():
    articles_path = os.path.join(DATA_DIR, "articles.json")
    if not os.path.exists(articles_path):
        print(f"❌ {articles_path} 파일이 없습니다. fetch_news.py를 먼저 실행하세요.")
        sys.exit(1)

    verified = verify(articles_path)

    out_path = os.path.join(DATA_DIR, "verified_articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(verified, f, ensure_ascii=False, indent=2)

    print(f"✅ 검증된 기사 저장 → {out_path}")


if __name__ == "__main__":
    main()
