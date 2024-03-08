import os
from flask import Flask, flash, request, redirect, url_for, session, jsonify, send_file, make_response, g, render_template
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
from dotenv import load_dotenv
from google.cloud import secretmanager_v1beta1 as secretmanager
from sendgrid import SendGridAPIClient
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
import re
import pandas as pd
from io import StringIO
import requests
import json
# from gmail_api_function import send_email
import os.path


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# from google_auth_oauthlib.flow import InstalledAppFlow
import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def use_gmail_to_send(subject, content, address):
  """Sends emails based on subject and body.
  """
  creds = None
  # Authentication. Stored in token.json.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
#   if not creds or not creds.valid:
#     if creds and creds.expired and creds.refresh_token:
#       creds.refresh(Request())
#     else:
#       flow = InstalledAppFlow.from_client_secrets_file(
#           "credentials.json", SCOPES
#       )
#       creds = flow.run_local_server(port=0)
#     # Save the credentials for the next run
#     with open("token.json", "w") as token:
#       token.write(creds.to_json())
  else:
      raise Exception('no auth token')

  # API call
  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(content)

    message["To"] = address
    message["From"] = "erikvank05@gmail.com"
    message["Subject"] = subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message

#set up flask app
app = Flask(
    __name__,
    static_url_path='',
    static_folder='../frontend/build',
    template_folder='../frontend/build'
)
app.secret_key = os.getenv("SECRET-KEY")
#load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("GPT-API-KEY"))

#development branch
prod = os.environ.get('PROD')
allowed_origins = [
    "https://oversealabs.io",
] if prod == "PRODUCTION" else ["http://localhost:3000"]
CORS(app, resources={r"/*": {"origins": "*"}})
mail = Mail(app)
current_dir = os.path.dirname(os.path.abspath(__file__))


#setup domain
YOUR_DOMAIN = 'https://oversealabs.io' if prod == "PRODUCTION" else 'http://localhost:3000'
#FIXME: place service account in secret files location and load it from there
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)

@app.route('/delete-email', methods=['DELETE'])
def delete_email():
    try:
        if 'emails' not in session:
            session['emails'] = {}
            session['email_counter'] = 0    
        email_id = request.args.get("emailId")
        if email_id not in session['emails']:
            return jsonify({'error': 'Could not delete email: email ID does not exist'}), 400
        else:
            del session['emails'][email_id]
            return jsonify({}), 200
    except Exception as e:
        print('Error: ', str(e))
        return jsonify({'error': f'An error occurred'}), 500

@app.route('/get-email', methods=['GET'])
def get_email():
    try:
        if 'emails' not in session:
            session['emails'] = {}
            session['email_counter'] = 0
        email_id = request.args.get("emailId")
        if email_id not in session['emails']:
            return jsonify({'error': 'Could not get email: email ID does not exist'}), 400
        else:
            return jsonify({'email': session['emails'][email_id]}), 200
    except Exception as e:
        print('Error: ', str(e))
        return jsonify({'error': f'An error occurred'}), 500
    
@app.route('/list-emails', methods=['GET'])
def list_emails():
    try:
        if 'emails' not in session:
            session['emails'] = {}
            session['email_counter'] = 0
        return jsonify({'emails': session['emails']}), 200
    except Exception as e:
        print('Error: ', str(e))
        return jsonify({'error': f'An error occurred'}), 500
    
@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        csvStringIO = StringIO(request.json['data'])
        custom_data = pd.read_csv(csvStringIO, sep=",", header=0)
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
        return_emails = []

        for email in emails:
            res = requests.post(url, json = email)
            subject = res.json()['subject']
            content = res.json()['content']
            address = email['address']
            use_gmail_to_send(subject, content, address)
            try:
                return_emails.append({'customerName': email['customerName'], 'address': email['address'], 'subject': subject, 'content': content, 'time': datetime.now()})
            except Exception as e:
                print(e)
        
        
        return jsonify({'emails': return_emails}), 200


    except Exception as e:
        return jsonify({'error': f'An error occured: {e}'}), 500

@app.route('/generate-email', methods=['POST'])
def generate_email():
    try:
        if 'emails' not in session:
            session['emails'] = {}
            session['email_counter'] = 0
        # Get the JSON data from the request
        data = request.json

        # Access individual fields from the data
        marketer_name = data.get('marketerName', '')
        product_description = data.get('productDescription', '')
        company_name = data.get('companyName', '')
        company_description = data.get('companyDescription', '')
        customer_name = data.get('customerName', '')
        customer_age = data.get('customerAge', '')
        custom_attributes = data.get('customAttributes', [])

        prompt = f"""Write a persoanlized marketing email for {customer_name}, a {customer_age}-year-old customer of {company_name}, which is a company with the following description: {company_description}. You have the following information about the customer:\n"""
        for att in custom_attributes:
            prompt += att['attribute'] + ': ' + att['description'] + ',\n'
        prompt += " and remember to make the email as short and as personalized as possible."

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a skilled email writer on the marketing team named {marketer_name} working to create personalized customer emails to increase sales."},
                {"role": "user", "content": prompt}
            ],
        )
        # increment email ID
        session['email_counter'] += 1

        # create email to add to dict
        email = {}
        email['time_generated'] = datetime.now()
        try:
            subj = re.findall(r'Subject[^\n]*\n\n', completion.choices[0].message.content)[0][9:-2]
        except:
            raise Exception("Could not get subject from GPT output.")
        try:
            content = re.findall(r'\n\n[^"]*', completion.choices[0].message.content)[0][2:]
        except:
            raise Exception("Could not get content from GPT output.")
        email['subject'] = subj
        email['content'] = content

        # save to emails
        session['emails'][session['email_counter']] = email
        
        return jsonify({'subject': email['subject'], 'content': email['content']}), 200

    except Exception as e:
        # Handle exceptions if any
        print('Error:', str(e))
        return jsonify({'error': f'An error occurred'}), 500

if __name__ == "__main__":
    app.run(port=8080, debug=True)

