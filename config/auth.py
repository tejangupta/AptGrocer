import smtplib
import os
from email.mime.text import MIMEText
from functools import wraps
from flask import redirect, session, url_for
from dotenv import load_dotenv


def is_logged_in(redirect_url=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' in session:
                return f(*args, **kwargs)
            else:
                if redirect_url:
                    return redirect(url_for(redirect_url))
                else:
                    return redirect(url_for('login'))
        return decorated_function
    return decorator


# Define a function to send a verification email
def send_verification_email(email, verification_token):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    load_dotenv(os.path.join(base_dir, 'mail.env'))

    sender = os.environ.get('MY_EMAIL')
    password = os.environ.get('MY_PASSWORD')

    msg = MIMEText(f"Click the link to verify your email: http://127.0.0.1:5000/verify_email/{verification_token}\n\n")
    msg['Subject'] = 'Verify Your Email'
    msg['From'] = sender
    msg['To'] = email

    # Send the email
    with smtplib.SMTP('smtp.office365.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)
