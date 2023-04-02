from functools import wraps
from flask import redirect, session, url_for


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
