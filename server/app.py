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


#set up flask app
app = Flask(
    __name__,
    static_url_path='',
    static_folder='../frontend/build',
    template_folder='../frontend/build'
)
#FIXME: huge security vulnerability
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

        prompt = f"""Write a persoanlized marketing email for {company_name} with the following company description: {company_description}.\nThe product you are selling has this description: {product_description}. The customer you write to is {customer_name}, a {customer_age}-year-old.\nYou may use any or all of the following customer info: """
        for att in custom_attributes:
            prompt += att['attribute'] + ': ' + att['description'] + ',\n'
        prompt += "and remember to make the email as personal as possible.\nThe email must be less than 200 words. Make the subject of the email personalized as well."

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
            subj = re.findall(r'Subject[^\n]*\n\n', completion.choices[0].message.content)[9][:-2]
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

