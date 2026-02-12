#!/usr/bin/env bash
set -euo pipefail

FILE_PATH="${1:-newsletter_miso_daily.html}"

if [[ ! -f "$FILE_PATH" ]]; then
  echo "ERROR: file not found: $FILE_PATH"
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "ERROR: curl is required."
  exit 1
fi

if ! command -v rg >/dev/null 2>&1; then
  echo "ERROR: rg is required."
  exit 1
fi

USER_AGENT="Mozilla/5.0 (Macintosh; Intel Mac OS X) MisoDailyLinkChecker/1.0"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
STRICT_YESTERDAY="${STRICT_YESTERDAY:-1}"

if command -v gdate >/dev/null 2>&1; then
  YESTERDAY="$(gdate -d 'yesterday' '+%Y-%m-%d')"
elif date -v-1d '+%Y-%m-%d' >/dev/null 2>&1; then
  YESTERDAY="$(date -v-1d '+%Y-%m-%d')"
else
  YESTERDAY="$(date -d 'yesterday' '+%Y-%m-%d')"
fi

Y="${YESTERDAY:0:4}"
M0="${YESTERDAY:5:2}"
D0="${YESTERDAY:8:2}"
M=$((10#$M0))
D=$((10#$D0))
YMD_COMPACT="${Y}${M0}${D0}"
PATTERN_URL="${YMD_COMPACT}|${Y}-${M0}-${D0}|${Y}/${M0}/${D0}|${Y}\\.${M0}\\.${D0}"
PATTERN_BODY="${Y}년[[:space:]]*${M}월[[:space:]]*${D}일|${Y}년[[:space:]]*${M0}월[[:space:]]*${D0}일|${Y}-${M0}-${D0}|${Y}/${M0}/${D0}|${Y}\\.${M0}\\.${D0}|${YMD_COMPACT}"

mapfile -t URLS < <(rg -o 'href="https?://[^"]+"' "$FILE_PATH" | sed -E 's/^href="|"$//')

if [[ "${#URLS[@]}" -eq 0 ]]; then
  echo "No external links found in $FILE_PATH"
  exit 0
fi

echo "Checking ${#URLS[@]} links in $FILE_PATH"
echo "Date rule: yesterday only (${YESTERDAY})"
echo

FAIL_COUNT=0

for URL in "${URLS[@]}"; do
  SAFE_NAME="$(echo "$URL" | sed 's/[^a-zA-Z0-9]/_/g')"
  BODY_FILE="$TMP_DIR/${SAFE_NAME}.html"

  HTTP_CODE="$(curl -L --max-time 20 --connect-timeout 8 -A "$USER_AGENT" -sS -o "$BODY_FILE" -w '%{http_code}' "$URL" || true)"
  LINE_NO="$(rg -n --fixed-strings "$URL" "$FILE_PATH" | head -n1 | cut -d: -f1 || true)"

  STATUS="OK"
  REASON=""

  if [[ ! "$HTTP_CODE" =~ ^[23] ]]; then
    STATUS="FAIL"
    REASON="HTTP_${HTTP_CODE:-000}"
  fi

  if [[ "$STATUS" == "OK" ]] && rg -i -a -q \
    '페이지를 찾을 수 없습니다|요청하신 페이지를 찾을 수 없습니다|존재하지 않는 페이지|404 error|404 not found|not found|찾을 수 없' \
    "$BODY_FILE"; then
    STATUS="FAIL"
    REASON="NOT_FOUND_PAGE_TEXT"
  fi

  if [[ "$STATUS" == "OK" ]] && rg -i -a -q \
    '<title>.*(404|not found|error)' \
    "$BODY_FILE"; then
    STATUS="FAIL"
    REASON="ERROR_TITLE"
  fi

  if [[ "$STATUS" == "OK" ]] && [[ "$STRICT_YESTERDAY" == "1" ]]; then
    if ! (echo "$URL" | grep -Eq "$PATTERN_URL" || grep -Eia -q "$PATTERN_BODY" "$BODY_FILE"); then
      STATUS="FAIL"
      REASON="NOT_YESTERDAY_NEWS"
    fi
  fi

  if [[ "$STATUS" == "OK" ]]; then
    echo "[PASS] line ${LINE_NO:-?} | $HTTP_CODE | $URL"
  else
    echo "[FAIL] line ${LINE_NO:-?} | $REASON | $URL"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

echo
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo "Result: FAIL ($FAIL_COUNT broken/suspicious links)"
  echo "Action: Replace failed links before sending."
  exit 2
fi

echo "Result: PASS (all links reachable)"
