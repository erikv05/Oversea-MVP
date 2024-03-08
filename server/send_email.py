import pandas as pd
import requests
import json
from gmail_api_function import send_email

custom_data = pd.read_csv("oversea_test_data.csv")

for i in range(custom_data.shape[0]):
    emails = []
    custom_cols = []
    for j in range(7, custom_data.shape[1]):
        col = {}
        col["attribute"] = custom_data.columns[j]
        col["description"] = custom_data.iloc[i,j]
        custom_cols.append(col)
    email = {
        'companyDescription': custom_data.iloc[i]["Company Description"],
        'productDescription': custom_data.iloc[i]["Product Description"],
        'companyName': custom_data.iloc[i]["Company Name"],
        'customerAge': custom_data.iloc[i].astype("string")["Customer Age"],
        'marketerName': custom_data.iloc[i]["Marketer Name"],
        'customerName': custom_data.iloc[i]["Customer Name"],
        'address': custom_data.iloc[i]["Email"],
        'customAttributes': custom_cols
        }
    emails.append(email)

url = "http://127.0.0.1:8080/generate-email"

for email in emails:
    res = requests.post(url, json = email)
    subject = res.json()['subject']
    content = res.json()['content']
    address = email['address']
    #TODO: remove test code
    # subject = 'test subject'
    # content = 'test content'
    # address = 'erikvank05@gmail.com'
    send_email(subject, content, address)