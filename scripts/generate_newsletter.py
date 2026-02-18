#!/usr/bin/env python3
"""
generate_newsletter.py — verified_articles.json + 템플릿으로 최종 HTML을 생성합니다.
"""

import json
import os
import shutil
import sys
from datetime import datetime, timedelta

from jinja2 import Environment, FileSystemLoader

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


def get_weekly_calendar(today: datetime) -> list:
    """이번 주 월~금 날짜와 상태를 반환합니다."""
    # 이번 주 월요일 계산
    start_of_week = today - timedelta(days=today.weekday())
    
    calendar = []
    weekday_kr = ["월", "화", "수", "목", "금"]
    
    for i, day_name in enumerate(weekday_kr):
        current_day = start_of_week + timedelta(days=i)
        is_today = (current_day.date() == today.date())
        is_past = (current_day.date() < today.date())
        
        status = "future"
        if is_past:
            status = "checked"
        elif is_today:
            status = "today"
            
        calendar.append({
            "day_name": day_name,     # 월, 화, 수...
            "date": current_day.day,  # 16, 17, 18...
            "is_today": is_today,
            "status": status
        })
    return calendar


def build_headline(categories: list[dict]) -> str:
    """첫 번째 카테고리의 첫 번째 기사 제목에서 핵심 키워드를 추출합니다."""
    for cat in categories:
        for article in cat.get("articles", []):
            title = article.get("title", "")
            # 제목이 너무 길면 앞부분만
            if len(title) > 30:
                return title[:30] + "…"
            return title
    return "전일자 주요 뉴스 요약"


def build_briefing_points(categories: list[dict]) -> list[str]:
    """각 카테고리의 첫 번째 기사 제목을 시장 브리핑 포인트로 사용합니다."""
    points = []
    for cat in categories:
        articles = cat.get("articles", [])
        if articles:
            points.append(articles[0]["title"])
    if not points:
        points.append("전일자 주요 뉴스를 확인해 주세요.")
    return points[:4]


def main():
    # ── 데이터 로드 ──
    verified_path = os.path.join(DATA_DIR, "verified_articles.json")
    if not os.path.exists(verified_path):
        print(f"❌ {verified_path} 없음. verify_links.py를 먼저 실행하세요.")
        sys.exit(1)

    with open(verified_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    yesterday_str = data.get("date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
    yesterday = datetime.strptime(yesterday_str, "%Y-%m-%d")

    categories = data.get("categories", [])

    # ── 템플릿 변수 구성 ──
    now = datetime.now()
    context = {
        "today_display": now.strftime("%Y년 %m월 %d일 ") + WEEKDAY_KR[now.weekday()] + "요일",
        "yesterday_display": yesterday.strftime("%Y.%m.%d"),
        "calendar_week": get_weekly_calendar(now),
        "headline": build_headline(categories),
        "briefing_points": build_briefing_points(categories),
        "categories": categories,
    }

    # ── HTML 생성 ──
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("newsletter_template.html")
    html = template.render(**context)

    # ── 파일 저장 ──
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    newsletter_path = os.path.join(PUBLIC_DIR, "newsletter_miso_daily.html")
    index_path = os.path.join(PUBLIC_DIR, "index.html")

    with open(newsletter_path, "w", encoding="utf-8") as f:
        f.write(html)

    shutil.copy2(newsletter_path, index_path)

    total = sum(len(c.get("articles", [])) for c in categories)
    print(f"✅ 뉴스레터 생성 완료 ({total}건 기사)")
    print(f"   → {newsletter_path}")
    print(f"   → {index_path}")


if __name__ == "__main__":
    main()
