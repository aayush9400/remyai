from flask import Flask, redirect, url_for, session
import os
from routes import initialize_routes

app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

initialize_routes(app)

if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)
