# Import flask dependencies
from flask import Blueprint, request, render_template,\
    g, redirect, url_for
from flask import session as login_session

# Import password / encryption helper tools
from werkzeug import check_password_hash, generate_password_hash

# Import module forms
from app.mod_auth.forms import LoginForm

# Import module models
from app.models import User

# Import Random and String to create state token
import random
import string

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')


# Set the route and accepted methods
@mod_auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Create state token and places it inside session variable for
    later validation.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # If sign in form is submitted
    form = LoginForm(request.form)

    # Verify the sign in form
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_session['user.id'] = user.id
    return render_template('login.html', STATE=state, form=form)
