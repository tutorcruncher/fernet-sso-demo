#!/usr/bin/env python
import json

import click
from cryptography.fernet import Fernet


@click.group()
def cli():
    pass


@cli.command()
def generate_key():
    """Generate new Fernet key"""
    click.echo('new key: {}'.format(Fernet.generate_key().decode('utf8')))


@cli.command()
@click.argument('secret', nargs=1)
@click.argument('data', nargs=-1)
def create_token(secret, data):
    """Create token from data and secret"""
    obj = {}
    for d in data:
        key, value = d.split('=', 1)
        obj[key] = value

    f = Fernet(secret.encode('utf8'))
    j = json.dumps(obj)
    click.echo('data: {}'.format(j))
    token = f.encrypt(j.encode('utf8'))
    click.echo('Created SSO token:\n  ?token={}\n\n'.format(token.decode('utf8')))

if __name__ == '__main__':
    cli()
