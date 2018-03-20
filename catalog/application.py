#!/usr/bin/python2.7
from flask import (Flask,
                   render_template,
                   request,
                   redirect,
                   url_for,
                   flash,
                   jsonify)
from sqlalchemy import create_engine, asc, func, Date, desc
from sqlalchemy.orm import relationship, sessionmaker
from database_setup_app import Base, Category, Quote, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Pot Of Quotes App"

engine = create_engine('sqlite:///quotes.db')
Base.metadata.bind = create_engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    """
    Create state token and places it inside session variable for
    later validation.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places it inside a session
    variable.
    """
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)

    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID doesn't match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(data['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<img src="'
    output += login_session['picture']
    output += ' " class="user-pic-login rounded-circle" >'
    output += '<h2 class="col-md-12 sign-in__style app-title">Welcome,</h2> '
    output += "<p class='col-md-12 signin-greet'>"
    output += login_session['username']
    output += '</p>'

    flash("You are now logged in as %s" % login_session['username'])
    return output


# User helper Functions
def getUserID(email):
    """
    Verify with email if user is in database
    :param email:
    :return: User's id.
    """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    """
    Get user's information with the user_id provided.
    :param user_id:
    :return: User's stored information
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    """
    Create new user storing name, email and picture
    :param login_session:
    :return: User's id
    """
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
    """
    Only disconnect a connected user.
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps('Failed to revoke token for given'
                                            ' user'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/api/v1/categories')
def categoriesJSON():
    """
    API endpoint call for all categories
    First - check if user is logged-in if not redirect to '/login'
    :return: A list of categories in JSON format
    """
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in categories])


@app.route('/api/v1/categories/<string:category_name>/quotes')
def categoryAllQuotesJSON(category_name):
    """
    API endpoint call for quotes
    First - check if user is logged-in if not redirect to '/login'
    :param: category_name:
    :return: A list of quotes under category in JSON format
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(name=category_name).one()
    quotes = session.query(Quote).filter_by(category=category).all()
    return jsonify(quotes=[i.serialize for i in quotes])


@app.route('/api/v1/categories/<string:category_name>/quotes/<int:quote_id>')
def categoryQuoteJSON(category_name, quote_id):
    """
    API endpoint for single
    First - check if user is logged-in if not redirect to '/login'
    :param category_name:
    :param quote_id:
    :return: single quote in JSON format
    """
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(id=category_name).one()
    quote = session.query(Quote).filter_by(
        category=category, id=quote_id).one()
    return jsonify(Quote=quote.serialize)


# Landing Page
@app.route('/')
def landPage():
    return render_template('landingpage.html')


# Show all categories
@app.route('/categories/')
def showCategories():
    """
    Categories endpoint call
    :return: Alphabetical list of categories
    """
    categories = session.query(Category).order_by(asc(Category.name))
    quotes = session.query(Quote).order_by(
        desc(Quote.created_on)).limit(10).all()
    return render_template('categories.html',
                           categories=categories,
                           quotes=quotes)


# Show all quotes under category
@app.route('/categories/<string:category_name>/')
@app.route('/categories/<string:category_name>/quotes')
def showAllQuotes(category_name):
    """
    Quotes under a category endpoint call
    :param category_name:
    :return: Alphabetical list of quotes
    """
    categories = session.query(Category).order_by(
        asc(Category.name))
    category = session.query(Category).filter_by(
        name=category_name).one()
    quotes = session.query(Quote).filter_by(
        category=category).all()
    creator = getUserInfo(Quote.user_id)
    return render_template('quotes.html',
                           category=category,
                           categories=categories,
                           quotes=quotes,
                           creator=creator)


# Show selected quote under category
@app.route('/categories/<string:category_name>/quotes/<int:quote_id>')
def showQuote(category_name, quote_id):
    """
    Single quote endpoint call
    :param category_name:
    :param quote_id:
    :return: A single quote
    """
    category = session.query(Category).filter_by(
        name=category_name).one()
    quote = session.query(Quote).filter_by(id=quote_id).one()
    creator = getUserInfo(quote.user_id)

    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return render_template('publicquote.html',
                               quote=quote,
                               category=category,
                               creator=creator)
    else:
        return render_template('quote.html',
                               category=category,
                               quote=quote,
                               creator=creator)


# Add new quote under category
@app.route('/categories/<string:category_name>/quotes/new',
           methods=['GET', 'POST'])
def newQuote(category_name):
    """
    Add new quote for X category
    First - check if 'username' is logged-in if not redirect to '/login'
    :param category_name:
    :return: Form with 'author' and 'description'= quote, fields
    """
    if 'username' not in login_session:
        return redirect('/login')

    category = session.query(Category).filter_by(
        name=category_name).one()
    if request.method == 'POST':
        addNewQuote = Quote(author=request.form['author'],
                            description=request.form['description'],
                            category=category,
                            user_id=login_session['user_id'])
        session.add(addNewQuote)
        session.commit()
        flash('New Quote by Successfully Added')
        return redirect(url_for('showAllQuotes',
                                category_name=category_name))
    else:
        return render_template('newQuote.html',
                               category_name=category_name,
                               category=category)


# Edit quote selected under category
@app.route('/categories/<string:category_name>/quotes/<int:quote_id>/edit',
           methods=['GET', 'POST'])
def editQuote(category_name, quote_id):
    """
    Edit quote for X category
    First - check if 'username' is logged-in if not redirect to '/login'
    Second - verify that 'username' is the creator of quote.
    :param category_name:
    :param quote_id:
    :return: Form with 'author' and 'description'= quote, fields. Inside
    placeholders; current author and description for quote are
    visible for reference.
    """
    if 'username' not in login_session:
        return redirect('/login')

    editedQuote = session.query(Quote).filter_by(id=quote_id).one()
    category = session.query(Category).filter_by(name=category_name).one()
    creator = getUserInfo(Quote.user_id)

    if login_session['user_id'] != editedQuote.user_id:
        return "<script>function.myFunction() {alert('You are not authorized" \
               " to edit this quote. Add your favorite quotes and share " \
               "them with the world. Those you will be able to edit.');}" \
               "</script><body onload='myFunction()'>"

    if request.method == 'POST':
        if request.form['author']:
            editedQuote.author = request.form['author']
        if request.form['description']:
            editedQuote.description = request.form['description']
        session.add(editedQuote)
        session.commit()
        flash("Quote Successfully Edited")
        return redirect(url_for('showAllQuotes',
                                category_name=category_name))
    else:
        return render_template('editQuote.html',
                               category_name=category_name,
                               quote_id=quote_id,
                               quote=editedQuote,
                               creator=creator,
                               category=category)


# Delete quote selected under category
@app.route('/categories/<string:category_name>/quotes/<int:quote_id>/delete',
           methods=['GET', 'POST'])
def deleteQuote(category_name, quote_id):
    """
    Delete quote for X category
    First - check if 'username' is logged-in if not redirect to '/login'
    Second - verify that 'username' is the creator of quote
    :param category_name:
    :param quote_id:
    :return: Prompts with question to check if creator is sure of deleting
    quote.
    """
    if 'username' not in login_session:
        return redirect('/login')

    quoteToDelete = session.query(Quote).filter_by(id=quote_id).one()
    category = session.query(Category).filter_by(name=category_name).one()
    creator = getUserInfo(Quote.user_id)

    if login_session['user_id'] != quoteToDelete.user_id:
        return "<script>function myFunction() {alert('You are not authorized" \
               " to delete this quote. Add your favorite quotes and share " \
               "them with the world. Those you will be able to delete.');}" \
               "</script><body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(quoteToDelete)
        session.commit()
        flash("Quote Successfully Deleted")
        return redirect(url_for('showAllQuotes',
                                category_name=category_name))
    else:
        assert isinstance(category, object)
        return render_template('deleteQuote.html',
                               category_name=category_name,
                               quote=quoteToDelete,
                               creator=creator,
                               category=category)


@app.route('/disconnect')
def disconnect():
    """
    User login-out by deleting provider's credentials.
    :return: Returns user to the categories page
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()

        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
            del login_session['username']
            del login_session['email']
            del login_session['picture']
            del login_session['user_id']
            del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategories'))


if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=8000)
