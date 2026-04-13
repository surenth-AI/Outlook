import os
import msal
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORITY = os.getenv('AUTHORITY')
SCOPE = os.getenv('SCOPE', 'Mail.Read User.Read').split()

print(f"DEBUG: Attempting to fetch token for:")
print(f"  CLIENT_ID: {CLIENT_ID}")
print(f"  AUTHORITY: {AUTHORITY}")
print(f"  SCOPE: {SCOPE}")
# Do not print the full secret for security, but check if it exists
print(f"  CLIENT_SECRET exists: {bool(CLIENT_SECRET)}")
if CLIENT_SECRET:
    print(f"  CLIENT_SECRET starts with: {CLIENT_SECRET[:3]}...")
    print(f"  CLIENT_SECRET ends with: ...{CLIENT_SECRET[-3:]}")
    print(f"  CLIENT_SECRET length: {len(CLIENT_SECRET)}")

def test_token_acquisition():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, 
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    
    # We'll try acquire_token_for_client first (Client Credentials Flow) 
    # just to see if the secret is valid for the app
    print("\n--- Testing Client Credentials Flow (App-only) ---")
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" in result:
        print("SUCCESS: Client credentials flow worked! The secret is valid.")
    else:
        print("FAILED: Client credentials flow failed.")
        print(f"Error: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")

if __name__ == "__main__":
    test_token_acquisition()
