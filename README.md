# GoBar

Keyword-based navigation bar in front of a search engine (SearXNG by default).
Register it as a browser search engine, then type either:

| Input | Behavior |
| --- | --- |
| `go <keyword>` | 302 redirect to the matching entry in `hosts.yaml` |
| `go` (unknown/bare) | Render the keyword menu |
| anything else | 302 redirect to the configured search engine with `?q=<query>` |

## Routes

| Route | Purpose |
| --- | --- |
| `/` and `/search` | Main entry: `?q=<query>` dispatches as above |
| `/go/<keyword>` | Direct keyword redirect (used by the menu links) |
| `/help` | Instructions to add GoBar as a browser search engine |
| `/opensearch.xml` | OpenSearch description so Firefox/Chrome can auto-add the engine |

## Configuration

Everything lives in `hosts.yaml`; the file is hot-reloaded on change
(mtime check on every query), so edits take effect without a restart.

```yaml
# Search engine used for non-`go` queries.
search_url: "http://search.example-domain/search"

infra:                       # category -> keyword -> URL
  router: "https://router.example-domain"
  proxmox: "https://pxmx.example-domain"

media:
  jellyfin: "http://LAN_IP:8096"
```

- Categories (top-level mappings) group keywords in the menu page.
- A flat `keyword: URL` mapping at the top level also works; those entries
  are grouped under a trailing `other` category.
- `search_url` is reserved: it configures the search engine and never
  appears as a keyword.
- The `GOBAR_SEARCH_URL` environment variable overrides the YAML value.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `GOBAR_HOSTS_FILE` | `./hosts.yaml` | Path to the hosts file |
| `GOBAR_SEARCH_URL` | (unset) | Overrides `search_url` from `hosts.yaml` |
| `GOBAR_HOST` | `0.0.0.0` | Bind address |
| `GOBAR_PORT` | `5000` | Bind port |

## Running

### Docker

```sh
docker compose up -d --build
```

The compose file maps host port `5055` (override with `GOBAR_PORT`) and
bind-mounts `hosts.yaml` read-only so edits hot-reload inside the
container. Uncomment the `environment:` block in `docker-compose.yml`
only if you need to override `search_url` outside the YAML.

### Bare Python

```sh
pip install -r requirements.txt   # flask, pyyaml
python app.py
```

## Layout

```
app.py               Flask app: routing, hosts.yaml loading/hot-reload
hosts.yaml           Search engine + category/keyword/URL mappings
templates/           base.html, keyword_list.html, help.html, opensearch.xml
static/style.css     Menu/help styling
Dockerfile           python:3.13-slim image
docker-compose.yml   Single-service deployment
```

## Browser setup

Open `/help` on a running instance: it shows the exact URL to register.
Once registered with shortcut `go` (or as the default engine), the
address bar accepts `go jellyfin`, `go proxmox`, or any plain search.
