import os
import requests

key = os.getenv("TAVILY_API_KEY")

if not key:
    print("ERROR: TAVILY_API_KEY belum diatur.")
    raise SystemExit(1)

response = requests.post(
    "https://api.tavily.com/search",
    json={
        "api_key": key,
        "query": "site:indonesia.go.id Presiden Republik Indonesia saat ini Prabowo Subianto",
        "search_depth": "advanced",
        "max_results": 5,
    },
    timeout=30,
)

print("HTTP STATUS:", response.status_code)

if not response.ok:
    print(response.text)
    raise SystemExit(1)

data = response.json()
results = data.get("results", [])

print("JUMLAH HASIL:", len(results))

for i, item in enumerate(results, 1):
    print(f"\n[{i}] {item.get('title')}")
    print("URL:", item.get("url"))
    print("ISI:", item.get("content", "")[:500])