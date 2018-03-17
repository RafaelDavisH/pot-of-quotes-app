# Import Form
from flask.ext.wtf import Form

# Import Form elements such as TextField
from wrforms import TextField, PasswordField

# Import Form validators
from wtforms.validators import Required, Email, EqualTo


# Define the login form (WTForms)

class LoginForm(Form):
    email = TextField('Email Address', [Email(), Required(
        message='Forgot your email address?')])
    password = PasswordField('Password', [Required(
        message='Must provide a password. ;-)')])
