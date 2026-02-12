# Miso Daily 링크 필터링 가이드

발송 전 아래 명령으로 링크를 검사하세요.

```bash
chmod +x /Users/gimminsu/Desktop/miso_daily/check_newsletter_links.sh
/Users/gimminsu/Desktop/miso_daily/check_newsletter_links.sh /Users/gimminsu/Desktop/miso_daily/newsletter_miso_daily.html
```

## 필터링 기준
- `HTTP 2xx/3xx`가 아니면 실패
- 본문에 `페이지를 찾을 수 없습니다`, `404`, `not found` 등 에러 문구가 있으면 실패
- `<title>`에 `404`, `not found`, `error`가 있으면 실패
- **전일자(어제) 기사 날짜가 URL 또는 본문에서 확인되지 않으면 실패**

## 운영 권장 룰
- 결과가 `FAIL`이면 해당 기사 링크를 즉시 교체
- 발송 직전 1회, 발송 30분 전 1회 총 2회 검사
- 링크 출처는 국내 매체만 사용 (`.kr` 도메인 또는 국내 언론사)

## 참고 옵션
- 기본값은 전일자 검증 ON 입니다.
- 임시로 전일자 검증을 끄려면:

```bash
STRICT_YESTERDAY=0 /Users/gimminsu/Desktop/miso_daily/check_newsletter_links.sh /Users/gimminsu/Desktop/miso_daily/newsletter_miso_daily.html
```
