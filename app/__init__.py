# Import flask and template operators
from flask import Flask, render_template, request, redirect,\
    url_for, flash, jsonify
from sqlalchemy import create_engine, asc, func, Date, desc
from sqlalchemy.orm import relationship, sessionmaker
from app.models import Base

# Import a module / component using its blueprint handler variable (mod_auth)
from app.mod_auth.controllers import mod_auth as auth_module

CLIENT_ID = json.loads(
    open('client_secret.json' 'r').read())['web']['client_id']
APPLICATION_NAME = "Pot Of Quotes App"


app = Flask(__name__)

app.config.from_object('config')

Base.metadata.bind = create_engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


# Register blueprints
app.register_blueprint(auth_module)
