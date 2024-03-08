import pandas as pd
import requests
import json

url = "http://127.0.0.1:8080/list-emails"

res = requests.get(url)
print(res.json())