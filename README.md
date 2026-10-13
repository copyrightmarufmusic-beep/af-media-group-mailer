# CRY DIGITAL MEDIA — Mail Operations

## Included
- `fast_mailer.py`: enhanced Streamlit app, based on the uploaded original
- `backup/fast_mailer.py.original`: byte-for-byte backup of the original Python file
- `assets/`: provided CRY DIGITAL MEDIA logo and CEO profile image
- `requirements.txt`: Python dependencies

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `python -m pip install -r requirements.txt`
4. Run `python -m streamlit run fast_mailer.py`
5. Open the local URL printed in the terminal.

## Deploy
The app is prepared for Streamlit Community Cloud: push this folder to a private GitHub repository, then create a new app and choose `fast_mailer.py`. Keep SMTP credentials private and use a Gmail App Password. Deployment requires the account owner to authorize the hosting/GitHub connection.

## Safety and delivery notes
The app sends a finite batch (maximum 50 unique recipients per run) with a minimum 5-second interval and a confirmation step. It does not implement unlimited repeated sending. Session statistics reset when the session resets. SMTP acceptance is not proof of inbox delivery. No live SMTP test was run because that requires the owner's credentials and permission.
