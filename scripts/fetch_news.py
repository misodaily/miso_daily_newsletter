#!/usr/bin/env python3
"""
fetch_news.py — Naver News Search API를 사용하여 카테고리별 전일자 뉴스를 수집합니다.

환경 변수:
  NAVER_CLIENT_ID     — Naver 개발자 Client ID
  NAVER_CLIENT_SECRET — Naver 개발자 Client Secret
"""

import json
import os
import re
import sys
from datetime import datetime
from datetime import timedelta
from urllib.parse import quote

import requests

# ── 설정 ──────────────────────────────────────────────
CATEGORIES = [
    {
        "label": "🌍 거시경제 & 금융",
        "queries": ["코스피 마감 시황", "금감원 금융 제재", "한국은행 금리", "원달러 환율"],
        "max_articles": 3,
    },
    {
        "label": "💻 반도체/IT",
        "queries": ["삼성전자 반도체", "SK하이닉스 HBM", "반도체 수출 실적"],
        "max_articles": 3,
    },
    {
        "label": "🔋 2차전지/에너지",
        "queries": ["2차전지 배터리 수주", "LG에너지솔루션", "SK온 ESS"],
        "max_articles": 3,
    },
    {
        "label": "🛡️ 금융/배당/방어주",
        "queries": ["고배당주 ETF", "KB금융 배당", "주주환원 자사주"],
        "max_articles": 3,
    },
]

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def get_yesterday() -> str:
    """어제 날짜를 YYYY-MM-DD 형태로 반환합니다."""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def search_naver_news(query: str, client_id: str, client_secret: str, display: int = 10) -> list[dict]:
    """Naver 뉴스 검색 API를 호출합니다."""
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": display,
        "sort": "date",
    }
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("items", [])


def clean_html(text: str) -> str:
    """Naver API 응답의 HTML 태그(<b> 등)를 제거합니다."""
    return re.sub(r"<[^>]+>", "", text).strip()


def is_yesterday(link: str, pub_date_str: str, yesterday: str) -> bool:
    """기사가 전일자인지 확인합니다 (URL 패턴 + pubDate)."""
    ymd = yesterday.replace("-", "")  # 20260216
    y_dot = yesterday.replace("-", ".")  # 2026.02.16

    # URL에 날짜 포함 여부
    if ymd in link or y_dot in link or yesterday in link:
        return True

    # pubDate 파싱 (예: "Mon, 16 Feb 2026 09:00:00 +0900")
    try:
        pub_dt = datetime.strptime(pub_date_str.strip(), "%a, %d %b %Y %H:%M:%S %z")
        if pub_dt.strftime("%Y-%m-%d") == yesterday:
            return True
    except (ValueError, TypeError):
        pass

    return False


def fetch_all(client_id: str, client_secret: str) -> dict:
    """모든 카테고리에 대해 뉴스를 수집합니다."""
    yesterday = get_yesterday()
    print(f"[fetch_news] 수집 대상 날짜: {yesterday}")

    result = {"date": yesterday, "categories": []}

    for cat in CATEGORIES:
        articles = []
        seen_links = set()

        for query in cat["queries"]:
            try:
                items = search_naver_news(query, client_id, client_secret)
            except Exception as e:
                print(f"  ⚠ 검색 실패 ({query}): {e}")
                continue

            # Process items from the search result
            filtered_items = []
            for item in items:
                title = clean_html(item.get("title", ""))
                if not title:
                    continue

                # 🚀 [변경] 네이버 뉴스(news.naver.com) 링크만 수집합니다.
                # 외부 언론사 사이트는 링크가 죽거나(404), 리다이렉트 되는 경우가 많아 제외합니다.
                link = item.get("link", "")
                if "news.naver.com" not in link:
                    continue

                # 날짜 필터링 (전일자)
                pub_date_str = item.get("pubDate", "")
                if not is_yesterday(link, pub_date_str, yesterday): # Pass link to is_yesterday
                    continue
                
                # 중복 제거
                if link in seen_links:
                    continue
                seen_links.add(link)

                filtered_items.append({
                    "title": title,
                    "url": link,  # news.naver.com 링크 (changed from 'link' to 'url' to match original structure)
                    # "pubDate": pub_date_str, # Not needed in final articles list
                    # "description": clean_html(item.get("description", "")) # Not needed in final articles list
                })
            
            # Add filtered items to articles, respecting max_articles
            for article_item in filtered_items:
                if len(articles) >= cat["max_articles"]:
                    break
                articles.append(article_item)

            if len(articles) >= cat["max_articles"]:
                break

        print(f"  ✓ {cat['label']}: {len(articles)}건 수집")
        result["categories"].append({
            "label": cat["label"],
            "articles": articles,
        })

    return result


def main():
    client_id = os.environ.get("X_NAVER_CLIENT_ID", "")
    client_secret = os.environ.get("X_NAVER_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("❌ X_NAVER_CLIENT_ID / X_NAVER_CLIENT_SECRET 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    data = fetch_all(client_id, client_secret)

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, "articles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total = sum(len(c["articles"]) for c in data["categories"])
    print(f"\n✅ 총 {total}건 저장 → {out_path}")


if __name__ == "__main__":
    main()
