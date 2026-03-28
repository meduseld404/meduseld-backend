#!/bin/bash
# Scrape/mirror the Icarus wiki from wiki.gg for local hosting.
# Uses curl (which passes Cloudflare bot detection) instead of wget
# (which gets 403'd due to TLS fingerprinting).
#
# Strategy: fetch the Main_Page, extract wiki links, crawl them with
# curl, and download page requisites (CSS/JS/images).

WIKI_URL="https://icarus.wiki.gg"
WIKI_DIR="/srv/wiki/icarus"
TEMP_DIR="/srv/wiki/.scrape-tmp"
LOG_FILE="/srv/wiki/scrape.log"
LOCK_FILE="/tmp/wiki-scrape.lock"
MAX_PAGES=500
CRAWL_DELAY=1

# Prevent concurrent runs
if [ -f "$LOCK_FILE" ]; then
    pid=""
    pid=$(cat "$LOCK_FILE" 2>/dev/null) || true
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') Scrape already in progress (PID $pid), skipping." >> "$LOG_FILE" 2>/dev/null
        exit 0
    fi
    rm -f "$LOCK_FILE"
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE" 2>/dev/null
    echo "$1"
}

log "=== Starting wiki scrape from ${WIKI_URL} ==="

# Verify tools
for cmd in curl grep sed; do
    if ! command -v "$cmd" > /dev/null 2>&1; then
        log "ERROR: ${cmd} is not installed"
        exit 1
    fi
done

# Create directories
mkdir -p "$WIKI_DIR" "$TEMP_DIR/pages" "$TEMP_DIR/assets" 2>/dev/null
rm -rf "${TEMP_DIR:?}/"* 2>/dev/null || true
mkdir -p "$TEMP_DIR/pages" "$TEMP_DIR/assets" 2>/dev/null

# Test connectivity
log "Testing connectivity..."
HTTP_CODE=$(curl -sI -o /dev/null -w '%{http_code}' --max-time 15 "${WIKI_URL}/wiki/Main_Page" 2>/dev/null) || true
log "HTTP response code: ${HTTP_CODE:-timeout/error}"

if [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" = "000" ]; then
    log "ERROR: Cannot reach ${WIKI_URL}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

if [ "$HTTP_CODE" != "200" ]; then
    log "ERROR: ${WIKI_URL} returned ${HTTP_CODE}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# --- Crawl wiki pages using curl ---

VISITED_FILE="${TEMP_DIR}/.visited"
QUEUE_FILE="${TEMP_DIR}/.queue"
touch "$VISITED_FILE" "$QUEUE_FILE"

# Seed the queue with Main_Page
echo "/wiki/Main_Page" > "$QUEUE_FILE"

PAGE_COUNT=0

fetch_page() {
    local path="$1"
    local url="${WIKI_URL}${path}"
    # Create directory structure matching the URL path
    local safe_path
    safe_path=$(echo "$path" | sed 's|[?#].*||')  # strip query/fragment
    local file_path="${TEMP_DIR}/pages${safe_path}.html"
    local dir_path
    dir_path=$(dirname "$file_path")
    mkdir -p "$dir_path" 2>/dev/null

    curl -sL \
        --max-time 30 \
        --retry 2 \
        -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
        -H "Accept-Language: en-US,en;q=0.5" \
        -H "Accept-Encoding: identity" \
        -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
        -o "$file_path" \
        "$url" 2>/dev/null

    if [ -f "$file_path" ] && [ -s "$file_path" ]; then
        PAGE_COUNT=$((PAGE_COUNT + 1))
        # Extract wiki links from the page
        grep -oP 'href="/wiki/[^"#]*' "$file_path" 2>/dev/null | \
            sed 's|href="||g' | \
            grep -v -E '(Special:|User:|User_talk:|Talk:|File:|Template:|Category:.*action|index\.php)' | \
            sort -u >> "${TEMP_DIR}/.found_links" 2>/dev/null || true
        return 0
    else
        rm -f "$file_path" 2>/dev/null
        return 1
    fi
}

log "Crawling wiki pages..."

while [ "$PAGE_COUNT" -lt "$MAX_PAGES" ]; do
    # Get next unvisited URL from queue
    NEXT=""
    while IFS= read -r candidate; do
        if ! grep -qxF "$candidate" "$VISITED_FILE" 2>/dev/null; then
            NEXT="$candidate"
            break
        fi
    done < "$QUEUE_FILE"

    if [ -z "$NEXT" ]; then
        # Check if we found new links to add to queue
        if [ -f "${TEMP_DIR}/.found_links" ]; then
            # Merge found links into queue, dedup
            sort -u "${TEMP_DIR}/.found_links" "$QUEUE_FILE" > "${TEMP_DIR}/.queue_new" 2>/dev/null || true
            mv "${TEMP_DIR}/.queue_new" "$QUEUE_FILE" 2>/dev/null || true
            rm -f "${TEMP_DIR}/.found_links" 2>/dev/null
            # Try again
            NEXT=""
            while IFS= read -r candidate; do
                if ! grep -qxF "$candidate" "$VISITED_FILE" 2>/dev/null; then
                    NEXT="$candidate"
                    break
                fi
            done < "$QUEUE_FILE"
        fi
        if [ -z "$NEXT" ]; then
            log "No more pages to crawl"
            break
        fi
    fi

    # Mark as visited
    echo "$NEXT" >> "$VISITED_FILE"

    # Fetch the page
    fetch_page "$NEXT" || true

    # Merge any newly found links periodically
    if [ -f "${TEMP_DIR}/.found_links" ] && [ $((PAGE_COUNT % 10)) -eq 0 ]; then
        sort -u "${TEMP_DIR}/.found_links" "$QUEUE_FILE" > "${TEMP_DIR}/.queue_new" 2>/dev/null || true
        mv "${TEMP_DIR}/.queue_new" "$QUEUE_FILE" 2>/dev/null || true
        rm -f "${TEMP_DIR}/.found_links" 2>/dev/null
    fi

    # Progress logging
    if [ $((PAGE_COUNT % 25)) -eq 0 ] && [ "$PAGE_COUNT" -gt 0 ]; then
        QUEUE_SIZE=$(wc -l < "$QUEUE_FILE" 2>/dev/null) || true
        VISITED_SIZE=$(wc -l < "$VISITED_FILE" 2>/dev/null) || true
        log "Progress: ${PAGE_COUNT} pages fetched, ${VISITED_SIZE:-?} visited, ${QUEUE_SIZE:-?} in queue"
    fi

    # Be polite
    sleep "$CRAWL_DELAY"
done

# Final merge of found links
if [ -f "${TEMP_DIR}/.found_links" ]; then
    sort -u "${TEMP_DIR}/.found_links" "$QUEUE_FILE" > "${TEMP_DIR}/.queue_new" 2>/dev/null || true
    mv "${TEMP_DIR}/.queue_new" "$QUEUE_FILE" 2>/dev/null || true
fi

log "Crawled ${PAGE_COUNT} wiki pages"

if [ "$PAGE_COUNT" -lt 1 ]; then
    log "ERROR: No pages fetched"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# --- Download CSS/JS/images referenced by the pages ---
log "Downloading page assets..."
ASSET_COUNT=0

# Extract asset URLs from all HTML files
find "${TEMP_DIR}/pages" -name "*.html" -print0 2>/dev/null | \
    xargs -0 grep -ohP '(href|src)="(/[^"]+\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot))[^"]*"' 2>/dev/null | \
    sed 's|.*"\(/[^"]*\)"|\1|' | \
    sed 's|[?#].*||' | \
    sort -u > "${TEMP_DIR}/.assets" 2>/dev/null || true

TOTAL_ASSETS=$(wc -l < "${TEMP_DIR}/.assets" 2>/dev/null) || true
log "Found ${TOTAL_ASSETS:-0} unique assets to download"

while IFS= read -r asset_path; do
    [ -z "$asset_path" ] && continue
    local_path="${TEMP_DIR}/pages${asset_path}"
    local_dir=$(dirname "$local_path")
    mkdir -p "$local_dir" 2>/dev/null

    if [ ! -f "$local_path" ]; then
        curl -sL --max-time 15 --retry 1 \
            -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
            -o "$local_path" \
            "${WIKI_URL}${asset_path}" 2>/dev/null || true
        if [ -f "$local_path" ] && [ -s "$local_path" ]; then
            ASSET_COUNT=$((ASSET_COUNT + 1))
        else
            rm -f "$local_path" 2>/dev/null
        fi
    fi
done < "${TEMP_DIR}/.assets" 2>/dev/null || true

log "Downloaded ${ASSET_COUNT} assets"

# --- Rewrite links to be relative/local ---
log "Rewriting links for local browsing..."
find "${TEMP_DIR}/pages" -name "*.html" -print0 2>/dev/null | xargs -0 -r sed -i \
    -e "s|https://icarus.wiki.gg/wiki/|/wiki/|g" \
    -e "s|https://icarus.wiki.gg/||g" \
    -e "s|//icarus.wiki.gg/||g" \
    2>/dev/null || true

# --- Post-process: strip edit/login/tracking ---
log "Post-processing HTML files..."
find "${TEMP_DIR}/pages" -name "*.html" -print0 2>/dev/null | xargs -0 -r sed -i \
    -e 's|<script[^>]*google[^>]*>.*</script>||g' \
    -e 's|<script[^>]*analytics[^>]*>.*</script>||g' \
    -e '/<li[^>]*id="ca-edit"[^>]*>/,/<\/li>/d' \
    -e '/<li[^>]*id="ca-viewsource"[^>]*>/,/<\/li>/d' \
    -e '/<div[^>]*id="p-login"[^>]*>/,/<\/div>/d' \
    2>/dev/null || true

# --- Inject mirror banner ---
if command -v perl > /dev/null 2>&1; then
    find "${TEMP_DIR}/pages" -name "*.html" -print0 2>/dev/null | xargs -0 -r perl -pi -e '
        s{(<body[^>]*>)}{$1<style>.mw-mirror-banner{background:#1a1a2e;color:#e6c65c;text-align:center;padding:6px 12px;font-size:0.8rem;border-bottom:1px solid #e6c65c33;position:sticky;top:0;z-index:1000}.mw-mirror-banner a{color:#e6c65c}</style><div class="mw-mirror-banner">\x{1f4d6} Local mirror hosted by <a href="https://services.meduseld.io">Meduseld</a></div>}i;
    ' 2>/dev/null || true
fi

# --- Create index.html redirect ---
MAIN_PAGE=""
MAIN_PAGE=$(find "${TEMP_DIR}/pages" -path "*/wiki/Main_Page*" -name "*.html" 2>/dev/null | head -1) || true
if [ -n "$MAIN_PAGE" ]; then
    REL_PATH=$(realpath --relative-to="${TEMP_DIR}/pages" "$MAIN_PAGE" 2>/dev/null) || true
    if [ -n "$REL_PATH" ]; then
        cat > "${TEMP_DIR}/pages/index.html" << INDEXEOF
<!DOCTYPE html>
<html><head><meta http-equiv="refresh" content="0;url=${REL_PATH}"><title>Icarus Wiki</title></head>
<body><a href="${REL_PATH}">Go to wiki</a></body></html>
INDEXEOF
    fi
fi

# --- Swap in the new mirror ---
SCRAPED_DIR="${TEMP_DIR}/pages"
BACKUP_DIR="/srv/wiki/.icarus-backup"
rm -rf "$BACKUP_DIR" 2>/dev/null || true
if [ -d "$WIKI_DIR" ]; then
    mv "$WIKI_DIR" "$BACKUP_DIR" 2>/dev/null || true
fi
mv "$SCRAPED_DIR" "$WIKI_DIR" 2>/dev/null || true
rm -rf "$BACKUP_DIR" 2>/dev/null || true

# Write sync timestamp
date -u '+%Y-%m-%dT%H:%M:%SZ' > "${WIKI_DIR}/.last-sync" 2>/dev/null || true

# Cleanup
rm -rf "$TEMP_DIR" 2>/dev/null || true

FINAL_COUNT=0
FINAL_COUNT=$(find "$WIKI_DIR" -name "*.html" 2>/dev/null | wc -l) || true
TOTAL_SIZE=$(du -sh "$WIKI_DIR" 2>/dev/null | cut -f1) || true
log "Wiki scrape complete: ${FINAL_COUNT} pages, ${ASSET_COUNT} assets, ${TOTAL_SIZE:-unknown} total"
log "=== Scrape finished ==="
