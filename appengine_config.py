#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import sys
import logging
from google.appengine.api.app_identity import *
ON_DEV = False
ON_TEST = False
try:
  ON_DEV = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
  ON_TEST = "test" in get_application_id()
except:
  pass
import fixpath

#########################################
# Remote_API Authentication configuration.
#
# See google/appengine/ext/remote_api/handler.py for more information.
# For datastore_admin datastore copy, you should set the source appid
# value.  'HTTP_X_APPENGINE_INBOUND_APPID', ['trusted source appid here']
#
remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = (
    'HTTP_X_APPENGINE_INBOUND_APPID', ['test-pappa-mi'])

#def webapp_add_wsgi_middleware(app):
    #from google.appengine.ext.appstats import recording
    #app = recording.appstats_wsgi_middleware(app)
    #return app
	
logging.info("Dev: " + str(ON_DEV))
logging.info("Test: " + str(ON_TEST))

engineauth = {
    # Login uri. The user will be returned here if an error occures.
    'login_uri': '/eauth/login', # default 'login/'
    #'base_uri': '/', # this the base url for strategies. For example the login for facebook would now be '/routing/auth/facebook' and the callback would now be '/routing/auth/facebook/callback'. This isn't very well tested, so you might run into some problems. 
    # The user is sent here after successfull authentication.    
    'success_uri': '/',
    #'success_uri': '/routing/successful_login', # where the user is redirected to on successful login 
    'secret_key': 'SECRET1234567890SECRET',
    # Change to provide a subclassed model
    'user_model': 'engineauth.models.User',
}

if ON_TEST:
    engineauth['provider.google'] = {
        'client_id': '485876442157.apps.googleusercontent.com',
        'client_secret': 'UQXzPTqM7VI2dtrl7g4dMmxu',
        'api_key': 'AIzaSyCsKTyyDrbvwFLwaopx_uTWMlywHLm_hlw',
        }
else:
    engineauth['provider.google'] = {
        'client_id': '610506648671.apps.googleusercontent.com',
        'client_secret': '_oIxbi9__8RR8mG8bl40dByM',
        'api_key': 'AIzaSyDK9TuhnLfxxE1h16ar_B6Gztb0bkmBSuQ',
        }

engineauth['provider.linkedin'] = {
    'client_id': 't1cwngi8jvu3',
    'client_secret': 'EPATNWulLpb3uSGf',
    }

engineauth['provider.twitter'] = {
    'client_id': 'sZNyh2yNBksgOGnaXzNng',
    'client_secret': '6TmVX9Zv4orEQBJ371tVK1AhRIj9klMDHHBhKkHus',
    }
if ON_TEST:
    engineauth['provider.facebook'] = {
        'client_id': '107351225976615',
        'client_secret': '4eb5ead5aea491cde2922af03e856aea',
        'scope': 'email',
        }
else:
    engineauth['provider.facebook'] = {
        'client_id': '103254759720309',
        'client_secret': 'e57edc34abb15fece9abcc7b00d39735',
        'scope': 'email',
        }

engineauth['provider.windowslive'] = {
    'client_id': '0000000044089B00',
    'client_secret': 'Dpv8pn1-BbZGx8o1ZLrG7v1kJ4ZQTy21',
    }

appstats_MAX_STACK = 15

def webapp_add_wsgi_middleware(app):
    from engineauth import middleware
    #from google.appengine.ext.appstats import recording
    #app = recording.appstats_wsgi_middleware(app)
    app = middleware.AuthMiddleware(app)
    return app

