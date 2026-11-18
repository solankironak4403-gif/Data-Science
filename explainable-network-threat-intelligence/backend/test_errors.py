import json
import urllib.request
import urllib.error

URL = "http://127.0.0.1:8000/predict"


def post(name, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"{name}: HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8")[:150]
        print(f"{name}: HTTP {e.code} -> {text}")


post("Test 1 empty flows list", {"flows": []})
post("Test 2 missing columns", {"flows": [{"flow_duration": 1.0}]})
post("Test 3 wrong body", {"hello": "world"})