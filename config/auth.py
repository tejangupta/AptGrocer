import smtplib
import os
from email.mime.text import MIMEText
from functools import wraps
from flask import redirect, session, url_for
from dotenv import load_dotenv


class EmailSender:
    def __init__(self):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        load_dotenv(os.path.join(base_dir, 'mail.env'))
        self.sender = os.environ.get('MY_EMAIL')
        self.password = os.environ.get('MY_PASSWORD')

    def send_email(self, subject, recipient, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = recipient

        # Send the email
        with smtplib.SMTP('smtp.office365.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.sender, self.password)
            smtp.send_message(msg)

    def send_verification_email(self, email, verification_token):
        body = f"Click the link to verify your email: http://127.0.0.1:5000/verify_email/{verification_token}\n\n"
        self.send_email('Verify Your Email', email, body)


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
