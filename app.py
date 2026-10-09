"""GoBar — keyword-based navigation in front of SearXNG.

Routing:
  go <keyword>  -> redirect to hosts.yaml entry, or render keyword list if unknown
  <query>       -> redirect to the search engine configured in hosts.yaml
  /help         -> browser search-engine setup instructions
"""
import os
import threading
from urllib.parse import quote_plus

import yaml
from flask import Flask, redirect, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOSTS_FILE = os.environ.get("GOBAR_HOSTS_FILE", os.path.join(BASE_DIR, "hosts.yaml"))
ENV_SEARCH_URL = os.environ.get("GOBAR_SEARCH_URL")  # optional override of hosts.yaml
PREFIX = "go"

app = Flask(__name__)

_hosts = {}          # flat keyword -> url lookup
_categories = []     # [(category, [(keyword, url), ...]), ...] for the menu
_search_url = ENV_SEARCH_URL  # active engine: env override or hosts.yaml search_url
_hosts_lock = threading.Lock()
_hosts_mtime = None


def load_hosts(force=False):
    """Load hosts.yaml at startup and reload when the file changes.

    Accepts nested form (category -> keyword -> url) or flat (keyword -> url).
    """
    global _hosts, _categories, _hosts_mtime, _search_url
    try:
        mtime = os.stat(HOSTS_FILE).st_mtime
    except OSError:
        return _hosts
    if force or mtime != _hosts_mtime:
        with open(HOSTS_FILE, "r") as f:
            data = yaml.safe_load(f) or {}
        flat = {}
        categories = []
        search_url = None
        for name, value in data.items():
            if isinstance(value, dict):
                items = []
                for kw, url in value.items():
                    kw = str(kw).strip().lower()
                    flat[kw] = str(url).strip()
                    items.append((kw, str(url).strip()))
                if items:
                    categories.append((str(name).strip(), items))
            else:
                kw = str(name).strip().lower()
                if kw == "search_url":
                    search_url = str(value).strip()
                    continue
                flat[kw] = str(value).strip()
                categories.append(("other", [(kw, str(value).strip())]))
        # Merge flat entries into a single trailing "other" category.
        grouped = [(cat, items) for cat, items in categories if len(items) > 1 or cat != "other"]
        others = [i for cat, items in categories if cat == "other" for i in items]
        if others:
            grouped.append(("other", sorted(others)))
        with _hosts_lock:
            _hosts = flat
            _categories = grouped
            _hosts_mtime = mtime
            if ENV_SEARCH_URL or search_url:
                _search_url = ENV_SEARCH_URL or search_url
    return _hosts


def handle_query(query):
    query = (query or "").strip()
    hosts = load_hosts()
    if not query:
        return render_template("keyword_list.html", categories=_categories)

    parts = query.split(None, 1)
    if parts and parts[0].lower() == PREFIX:
        keyword = parts[1].strip().lower() if len(parts) > 1 else ""
        url = hosts.get(keyword)
        if url:
            return redirect(url)
        # Unknown keyword (or bare "go"): show the menu.
        return render_template("keyword_list.html", categories=_categories)

    with _hosts_lock:
        search_url = _search_url
    if search_url:
        return redirect(f"{search_url}?q={quote_plus(query)}", code=302)
    # No search engine configured: fall back to the keyword menu.
    return render_template("keyword_list.html", categories=_categories)


@app.route("/")
def index():
    return handle_query(request.args.get("q", ""))


@app.route("/search")
def search():
    return handle_query(request.args.get("q", ""))


@app.route("/go/")
@app.route("/go/<path:keyword>")
def go(keyword=None):
    keyword = (keyword or request.args.get("q", "")).strip()
    url = load_hosts().get(keyword.lower())
    if url:
        return redirect(url)
    return render_template("keyword_list.html", categories=_categories)


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/opensearch.xml")
def opensearch():
    root = request.url_root.rstrip("/")
    return render_template(
        "opensearch.xml", root=root
    ), 200, {"Content-Type": "application/opensearchdescription+xml"}


load_hosts(force=True)

if __name__ == "__main__":
    app.run(
        host=os.environ.get("GOBAR_HOST", "0.0.0.0"),
        port=int(os.environ.get("GOBAR_PORT", "5000")),
    )
