import re
import requests
from datetime import datetime, timedelta

def check_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    urls = re.findall(r'href="(https?://[^"]+)"', content)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    results = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"Checking {len(urls)} links...")
    for url in urls:
        if 'subscribe_miso_daily.html' in url:
            continue
        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code
            text = response.text
            
            # Simple check for "not found" text in body
            not_found_keywords = ["페이지를 찾을 수 없습니다", "존재하지 않는 페이지", "404 not found", "error"]
            is_dead_text = any(kw in text.lower() for kw in not_found_keywords)
            
            if status >= 400 or is_dead_text:
                results.append((url, f"DEAD (Status: {status}, Text: {is_dead_text})"))
            else:
                results.append((url, "OK"))
        except Exception as e:
            results.append((url, f"ERROR: {str(e)}"))

    for url, status in results:
        print(f"{status} | {url}")

if __name__ == "__main__":
    check_links('public/newsletter_miso_daily.html')
