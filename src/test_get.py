import truststore
truststore.inject_into_ssl()

import requests

URL = "https://example.com"
headers = {"User-Agent": "TFM-MUISD-scraper/0.1"}

r = requests.get(URL, headers=headers, timeout=20)
print("Status:", r.status_code)
print("Length:", len(r.text))