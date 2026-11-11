import json
import os
import urllib.error
import urllib.parse
import urllib.request

GRAPH_URL = "https://graph.facebook.com"
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def load_token(path=ENV_PATH):
    """Read FB_ACCESS_TOKEN from the environment, falling back to the .env file."""
    token = os.environ.get("FB_ACCESS_TOKEN")
    if token:
        return token.strip()
    with open(path, encoding="utf-8") as f:
        for line in f:
            key, sep, value = line.partition("=")
            if sep and key.strip() == "FB_ACCESS_TOKEN":
                return value.strip().strip("\"'")
    raise RuntimeError("FB_ACCESS_TOKEN not found in environment or .env")


def graph_get(path, token=None, **params):
    """GET a Graph API endpoint and return the parsed JSON response.

    Example: graph_get("me", fields="id,name")
    Errors from Facebook come back as {"error": {...}} rather than raising.
    """
    params["access_token"] = token or load_token()
    url = f"{GRAPH_URL}/{path.lstrip('/')}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        return json.load(e)


if __name__ == "__main__":
    print(json.dumps(graph_get("me", fields="id,name"), indent=2))
    print(json.dumps(graph_get("me/accounts", fields="id,name,fan_count"), indent=2))
