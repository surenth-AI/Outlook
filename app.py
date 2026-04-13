import os
import uuid
import requests
from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from flask_session import Session
import msal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
Session(app)

# MSAL configuration - stripping whitespace to prevent common copy-paste errors
CLIENT_ID = os.getenv('CLIENT_ID', '').strip()
CLIENT_SECRET = os.getenv('CLIENT_SECRET', '').strip()
TENANT_ID = os.getenv('TENANT_ID', 'common').strip()
# Use specific tenant authority if available, otherwise fallback to common
_AUTHORITY_URL = os.getenv('AUTHORITY')
if not _AUTHORITY_URL:
    _AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORITY = _AUTHORITY_URL.strip()

REDIRECT_PATH = os.getenv('REDIRECT_PATH', '/getAToken').strip()
ENDPOINT = os.getenv('ENDPOINT', 'https://graph.microsoft.com/v1.0/me/messages').strip()

# MSAL filters out reserved scopes like offline_access, openid, profile as it handles them internally.
# Explicitly passing them to certain MSAL methods causes a ValueError.
RESERVED_SCOPES = ['offline_access', 'openid', 'profile']
_RAW_SCOPE = os.getenv('SCOPE', 'Mail.Read User.Read').split()
SCOPE = [s.strip() for s in _RAW_SCOPE if s.lower().strip() not in RESERVED_SCOPES]
MOCK_MODE = os.getenv('MOCK_MODE', 'False').lower().strip() == 'true'

def _get_redirect_uri():
    # Use environment variable override if available, otherwise generate from url_for
    uri = os.getenv('REDIRECT_URI') or url_for('authorized', _external=True)
    print(f"DEBUG: Using redirect_uri: {uri}")
    return uri

def _build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY,
        client_credential=CLIENT_SECRET, token_cache=cache)

def _get_token_from_cache(scope=None):
    cache = msal.SerializableTokenCache()
    if session.get('token_cache'):
        cache.deserialize(session.get('token_cache'))
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:
        result = cca.acquire_token_silent(scope, account=accounts[0])
        return result
    return None

@app.route('/')
def index():
    if not session.get('user'):
        return render_template('index.html', user=None)
    return render_template('index.html', user=session.get('user'))

@app.route('/login')
def login():
    if MOCK_MODE:
        session['user'] = {'name': 'Demo User', 'preferred_username': 'demo@example.com'}
        return redirect(url_for('index'))
        
    session['state'] = str(uuid.uuid4())
    auth_url = _build_msal_app().get_authorization_request_url(
        SCOPE,
        state=session['state'],
        redirect_uri=_get_redirect_uri()
    )
    return redirect(auth_url)

@app.route(REDIRECT_PATH)
def authorized():
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('index'))
    
    if 'error' in request.args:
        return render_template('auth_error.html', error=request.args.get('error_description'))

    if request.args.get('code'):
        cache = msal.SerializableTokenCache()
        cca = _build_msal_app(cache=cache)
        result = cca.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=SCOPE,
            redirect_uri=_get_redirect_uri()
        )
        if 'error' in result:
            return render_template('auth_error.html', error=result.get('error_description'))
        
        session['user'] = result.get('id_token_claims')
        session['token_cache'] = cache.serialize()
    
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(
        AUTHORITY + '/oauth2/v2.0/logout' +
        '?post_logout_redirect_uri=' + url_for('index', _external=True)
    )

@app.route('/get_emails')
def get_emails():
    if MOCK_MODE:
        return jsonify({
            "value": [
                {
                    "subject": "Welcome to SleekMail! ✨",
                    "from": {"emailAddress": {"name": "Antigravity", "address": "ai@sleekmail.com"}},
                    "bodyPreview": "Welcome to your new inbox experience. This is a mock email to show you how beautiful your inbox will look once you connect Outlook.",
                    "receivedDateTime": "2026-04-13T10:00:00Z"
                },
                {
                    "subject": "Project Update: Azure Registration 🚀",
                    "from": {"emailAddress": {"name": "Microsoft Support", "address": "support@azure.com"}},
                    "bodyPreview": "We noticed you are setting up your app registration. Don't forget to copy your client secret value before leaving the page!",
                    "receivedDateTime": "2026-04-13T09:30:00Z"
                },
                {
                    "subject": "Quarterly Logistics Report 🚢",
                    "from": {"emailAddress": {"name": "Logistics Team", "address": "shipping@global.com"}},
                    "bodyPreview": "The Q1 report is ready for your review. Please see the attached Excel sheet for container tracking details.",
                    "receivedDateTime": "2026-04-13T08:15:00Z"
                }
            ]
        })

    token = _get_token_from_cache(SCOPE)
    if not token:
        return redirect(url_for('login'))
    
    # Fetch user profile for some context
    headers = {'Authorization': 'Bearer ' + token['access_token']}
    graph_data = requests.get(ENDPOINT, headers=headers).json()
    
    return jsonify(graph_data)

if __name__ == '__main__':
    app.run(debug=True)
