# Fernet SSO Demo

Flask based demonstration of TutorCruncher's Single-Sign-On feature.

The encryption and signature are accomplished using the [Fernet](https://github.com/fernet) symmetric encryption 
method (Fernet is available in numerous modern languages including python, ruby, go and javascript and 
is based on industry standard encryption algorithms).

This approach has a number of advantages:
* the token serves two purposes: it confirms that the user has come directly from TutorCruncher and provides some of their credentials eg. name & role.
* more or less any data required can be passed to the SSO addon: here user role type, name, id and appointment id are passed. The limit here is browser url length (generally [2000](http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers) characters), for reference the url in the example is 220 characters long.
* other data could be added to the token without breaking existing integrations
* no API integration is initially required to integrate as all required information is passed in the token
* token expiry can easily be adding without breaking any implementation as this feature is built into Fernet. 

A simple example is included below (this is in python but the equivalent would be very similar in any other language).

## Token workflow

Below is a simple example of the workflow (this is in python but the equivalent would be 
very similar in any other language):

```python
from cryptography.fernet import Fernet
import json

obj = {'rt': 'Contractor', 'nm': 'Samuel Colvin', 'id': 123, 'apt': 321}
shared_secret_key = '38mnLQKJf5J0J0Il4-wHr-KnMnjAz8cZLTvDHEAwU-c='
f = Fernet(shared_secret_key)
token = f.encrypt(json.dumps(obj))
url = 'http://www.example.com/tc-sso?token=%s' % token

# url: http://www.example.comsso-lander/testing?token=gAAAAABXBOTJZGO_-1ORdEHFSktCrUXVNNgMEIjc6IrlDyjjPzPAkn36S2-4-fKG1eFT1DlGUjAgTD3SLsO1XCgh-6MIj0x0bTYuXtrRKvu1Y6XPY8QDXWAm5B9Qr8NoThnhUZ3P36vBisUvusQaz8xQSqy26dU5rrMZ3X9YR6hdiuV-VUqM1Qw=

# on other server

f = Fernet(shared_secret_key)  # from your storage

obj2 = json.loads(f.decrypt(url.split('token=')[-1])  # should really use a proper url parser
# obj2: {u'apt': 321, u'id': 123, u'nm': u'Samuel Colvin', u'rt': u'Contractor'}
```

## Usage

This is just a simply proof of concept app which lets users "log in" and view who else has logged in.

The only extra complexity it adds which real life applications may not have to implement is a screen to set a 
new SSO shared secret to make testing easier.

#### 1 Setup a secret

You can create a new group to login to by going to https://fernetsso.herokuapp.com/add-group. You can either
use the secret offered or supply your own, eg. from TutorCruncher's SSO Config or by calling `Fernet.generate_key()`.

If you're using the auto-created secret, record it for future use.

#### 2 Create the SSO token

You now need to created the encrypted token to login with. This can be done by the sign-in app like TutorCruncher.
 
If you don't have the app other setup you can use the `util.py` tool her to generate the token, eg:

```shell
./utils.py create_token <the sso secret> "nm=Samuel Colvin" rt=Contractor id=123
> data: {"rt": "Contractor", "nm": "Samuel Colvin", "id": "123"}
> Created SSO token:
>   ?token=<the token>
```

The `utils.py create_token` script can take any arbitary key:value pairs but this app requires the token to include
`nm` (name) and `rt` (role type).

#### 3 Go to the url

You can then use the token to sign in. Go to 

```
https://fernetsso.herokuapp.com/sso-lander/<group name>?token=<the token>
```

The group name is the name you supplied in setup 1 above.
