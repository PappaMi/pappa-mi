#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Pappa-Mi org
# Authors: R.Previtera
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


from py.base import *

import os
import cgi
import logging
import urllib
from datetime import date, datetime, time, timedelta
import wsgiref.handlers
import webapp2 as webapp


from google.appengine.ext.ndb import model
import webapp2 as webapp
from google.appengine.api import memcache
from google.appengine.api import mail

from py.gviz_api import *
from py.model import *
from py.modelMsg import *
from py.form import IspezioneForm, NonconformitaForm
from py.base import BasePage, CMMenuHandler, config, handle_404, handle_500

TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"

class MobileHandler(BasePage):

  def get(self):
    if self.get_current_user():
      self.redirect('/mobile/stream')
      
    template_values = {
      "main": "mobile/public.html"
    }
    self.getBase(template_values)
  def post(self):
    return self.get()

class MobileStreamHandler(BasePage):

  @reguser_required_mobile
  def get(self):

    template_values = {
      "main": "mobile/main.html"
    }
    self.getBase(template_values)
  def post(self):
    return self.get()

class MobileMenuHandler(BasePage):

  @reguser_required_mobile
  def get(self):

    template_values = {
      "main": "mobile/menu.html"
    }
    self.getBase(template_values)
  def post(self):
    return self.get()

class MobileCommissioniHandler(BasePage):

  def get(self):

    template_values = {
      "main": "mobile/commissioni.html"
    }
    self.getBase(template_values)
  def post(self):
    return self.get()


app = webapp.WSGIApplication([
    ('/mobile', MobileHandler),
    ('/mobile/stream', MobileStreamHandler),
    ('/mobile/menu', MobileMenuHandler),
    ('/mobile/commissioni', MobileCommissioniHandler)
  ], debug=os.environ['HTTP_HOST'].startswith('localhost'), config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
