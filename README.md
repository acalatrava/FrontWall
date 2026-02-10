# Web Shield

A security-focused service that sits in front of WordPress (or any website), crawls it, caches everything as static files, and serves them through a hardened server with a WAF, input sanitization, and configurable POST exceptions.

## Architecture

```
Internet → Nginx Proxy Manager (TLS) → Web Shield (port 8080) → Static Cache
                                                                ↓ (POST only)
                                                        Sanitizer + WAF
                                                                ↓
                                                          WordPress
```

**Admin UI** runs on port `8000` (internal access only).
**Shield server** runs on port `8080` (exposed via nginx).

## Features

- **Static Caching**: BFS crawler mirrors your WordPress site into static HTML, CSS, JS, and assets
- **URL Rewriting**: Absolute WordPress URLs are converted to relative paths
- **Form Detection**: Automatically detects forms during crawling and suggests POST rules
- **POST Exceptions**: Whitelist specific form endpoints with per-field validation and sanitization
- **WAF**: Blocks malicious bots, path traversal, SQL injection patterns, and WordPress-specific attack vectors
- **Input Sanitization**: Multi-layer sanitization (HTML stripping, XSS detection, SQL injection detection, type validation)
- **Security Headers**: CSP, HSTS, X-Frame-Options, and more injected into every response
- **Rate Limiting**: Token bucket per-IP with configurable global and per-endpoint limits
- **Honeypot Fields**: Catch bots filling hidden form fields
- **Admin UI**: Modern Vue 3 dashboard to manage sites, run crawls, configure rules, and deploy the shield
- **JWT Auth**: Protected admin panel with first-run setup wizard

## Quick Start

### With Docker Compose (recommended)

```bash
# Clone the repo
cp .env.example .env
# Edit .env and set a strong WS_SECRET_KEY

docker compose up -d

# Open http://localhost:8000 to access the admin UI
# First visit will prompt you to create an admin account
```

### Development Setup

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

The frontend dev server runs on port 3000 and proxies API calls to port 8000.

## Usage

1. **Create admin account** on first visit at `http://localhost:8000`
2. **Add a site**: Go to Sites → Add Site, enter your WordPress URL
3. **Run the crawler**: Go to the site's Crawler page and click "Start Crawl"
4. **Review pages**: Browse cached pages, add any missing URLs manually
5. **Configure POST rules**: Set up exceptions for contact forms with field whitelists
6. **Deploy the shield**: Go to Shield → Deploy to start serving on port 8080
7. **Point nginx** at port 8080 to serve the shielded site

## Nginx Proxy Manager Configuration

Point your domain's proxy host to the Web Shield container:

- **Forward Hostname/IP**: `webshield` (container name) or `localhost`
- **Forward Port**: `8080`
- **Websocket Support**: Not needed for the shield port
- **Block Common Exploits**: Optional (Web Shield already does this)

Keep port `8000` **internal only** — do not expose the admin UI publicly.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `WS_SECRET_KEY` | `change-me-in-production` | JWT signing key (use a strong random value) |
| `WS_ADMIN_PORT` | `8000` | Admin API + UI port |
| `WS_SHIELD_PORT` | `8080` | Shield server port |
| `WS_LOG_LEVEL` | `info` | Logging level |
| `WS_RATE_LIMIT_REQUESTS` | `60` | Global rate limit (requests per window) |
| `WS_RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window |
| `WS_MAX_REQUEST_SIZE_BYTES` | `1048576` | Max request body size (1MB) |
| `WS_CRAWLER_MAX_CONCURRENCY` | `5` | Max concurrent crawler requests |
| `WS_CRAWLER_DELAY_SECONDS` | `0.5` | Delay between crawler requests |
| `WS_CRAWLER_MAX_PAGES` | `10000` | Maximum pages to crawl |

## Security

Web Shield applies multiple layers of security:

1. **Static serving eliminates the WordPress attack surface** — no PHP execution, no database queries
2. **WAF blocks** known attack tools, path traversal, and WordPress-specific attack paths
3. **All POST data is sanitized** through field whitelisting, type validation, HTML stripping, and injection detection
4. **Security headers** (CSP, HSTS, X-Frame-Options, etc.) are injected into every response
5. **Rate limiting** prevents abuse on both GET and POST endpoints
6. **Honeypot fields** catch automated form submissions
7. **Dangerous file extensions** (.php, .env, .sql, .git, etc.) are blocked at the server level

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async), SQLite
- **Crawler**: httpx, BeautifulSoup4, lxml
- **Frontend**: Vue 3, Vite, TailwindCSS v4, Pinia
- **Security**: bleach, python-jose (JWT), passlib (bcrypt)
- **Deployment**: Docker, docker-compose
