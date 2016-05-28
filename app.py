import os
import json
from json import JSONDecodeError
import logging
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, request, redirect, render_template, session
from redis import Redis

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'this is not a secure secret')

TOKEN_SECRET = os.getenv('TOKEN_SECRET', '').encode('utf8')
if not TOKEN_SECRET:
    raise RuntimeError('no "TOKEN_SECRET" environment variable found')

fernet = Fernet(TOKEN_SECRET)

redis_cli = Redis()



@app.route('/')
def index():
    profile = session.get('profile')
    if not profile:
        return 'Permission Denied: you can sign in using TutorCruncher SSO', 403
    logins = [l.decode('utf8') for l in redis_cli.lrange('logins', 0, -1)]
    return render_template('page.jinja', profile=profile, logins=logins)


@app.route('/sso-lander')
def sso_lander():
    token = request.args.get('token', '').encode('utf8')

    try:
        data = fernet.decrypt(token)
    except InvalidToken:
        return '403: Invalid Token', 403

    try:
        data = json.loads(data.decode('utf8'))
    except JSONDecodeError:
        return '400: problem parsing json', 400
    session['profile'] = data

    redis_cli.lpush('logins', '{nm} ({rt}) logged in at {dt}'.format(dt=datetime.now(), **data))
    return redirect('/')


@app.route('/logout')
def logout():
    session.pop('profile')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
