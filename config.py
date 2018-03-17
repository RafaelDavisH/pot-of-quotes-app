from sqlalchemy import create_engine

# Define application directory
import os

# Enable the development environment
DEBUG = True
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define database
engine = create_engine('sqlite:///' + os.path.join(BASE_DIR, 'app.db'))
DATABASE_CONNECT_OPTIONS = {}

# Application threads
THREADS_PER_PAGE = 2

# Enable protection against CSRF
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = "secret"

# Secret key for singing cookies
SECRET_KEY = "secret"
