import os
import requests
import json
from flask import Flask, redirect, request

with open('config.json', 'r') as json_file:
    config = json.load(json_file)

app = Flask(__name__)
key1 = os.urandom(12).hex()
print(key1)
app.secret_key = key1

CLIENT_ID = config["user_credentials"]["xero_client_id"]
CLIENT_SECRET = config["user_credentials"]["xero_client_secret"]
REDIRECT_URI = config["user_credentials"]["xero_redirect_uri"]
AUTH_URL = "https://login.xero.com/identity/connect/authorize"
TOKEN_URL = "https://identity.xero.com/connect/token"
SCOPE = config["xero_params"]["scope"]

@app.route("/")
def home():
    return redirect(f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}")

@app.route("/callback")
def callback():
    code = request.args.get('code')
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=token_data)

    if response.status_code == 200:
        token_info = response.json()

        with open("xero_token.json", "w") as token_file:
            json.dump(token_info, token_file)
        return "Access token received and saved!"
    else:
        return "Error fetching access token!"

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
