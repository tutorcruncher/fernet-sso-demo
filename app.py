import os
import re
import json
import logging
from urllib.parse import urlparse
from json import JSONDecodeError
from datetime import datetime

from cryptography.fernet import Fernet, InvalidToken
from flask import Flask, request, redirect, render_template, session, flash
from redis import Redis

app = Flask(__name__)
app.logger.addHandler(logging.StreamHandler())

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'this is not a secure secret')

REDIS_URL = os.getenv('REDIS_URL', 'redis://h:@localhost:6379')
redis_url = urlparse(REDIS_URL)
redis_cli = Redis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password or None)


@app.route('/')
def index_view():
    """
    Route page which either shows a simple message if you're not logged in, or shows a log of
    recent events (eg. logins) to authenticated users.
    """
    group = session.get('group')
    if group:
        group_key = 'info:{}'.format(group)
        log = [l.decode('utf8') for l in redis_cli.lrange(group_key, 0, -1)]
    else:
        log = None
    return render_template('index.jinja', profile=session.get('profile'), log=log)


@app.route('/profile')
def profile_view():
    """
    Display details about an authenticated user's session.
    """
    profile = session.get('profile')
    if not profile:
        return 'Permission Denied: you can sign in using TutorCruncher SSO', 403
    return render_template('profile.jinja', profile=profile, group=session.get('group'))


@app.route('/add-group', methods=['GET', 'POST'])
def add_group_view():
    """
    Create a new "group" for SSO. Groups are simply a name and a secret key.
    """
    if request.method == 'POST':
        group = re.sub(r'\W', '', request.form['group-name'])
        group_key = 'secret:{}'.format(group)
        redis_cli[group_key] = request.form['secret']
        group_key = 'info:{}'.format(group)
        redis_cli.lpush(group_key, '{} group created {:%Y-%m-%d %H:%M:%S}'.format(group, datetime.now()))
        flash('Group {} created'.format(group))
        return redirect('/')
    else:
        return render_template('add_group.jinja', profile=session.get('profile'))


@app.route('/sso-lander/<group>')
def sso_lander_view(group):
    """
    Log a user into the system using a signed and encrypted get argument "token".
    """
    secret = redis_cli.get('secret:{}'.format(group))
    if not secret:
        return 'group not found', 404
    fernet = Fernet(secret)

    token = request.args.get('token', '').encode('utf8')
    try:
        data = fernet.decrypt(token)
    except InvalidToken:
        return '403: Invalid Token', 403

    try:
        data = json.loads(data.decode('utf8'))
    except JSONDecodeError:
        return '400: problem parsing json', 400

    session.update(
        profile=data,
        group=group,
    )

    group_key = 'info:{}'.format(group)
    redis_cli.lpush(group_key, '{nm} ({rt}) logged in at {dt:%Y-%m-%d %H:%M:%S}'.format(dt=datetime.now(), **data))
    return redirect('/')


@app.route('/logout')
def logout():
    """
    Log the user out.
    """
    session.pop('profile')
    session.pop('group')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
