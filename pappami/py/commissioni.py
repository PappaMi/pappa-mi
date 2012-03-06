#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from py.base import *

import os
import cgi
import logging
import wsgiref.handlers

from google.appengine.ext.ndb import model
from google.appengine.api import users
import webapp2 as webapp
from jinja2.filters import do_pprint
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail
import threading

from model import *

class CommissioniHandler(BasePage):

  def get(self):
    template_values = dict()
    geo = model.GeoPt(45.463681,9.188171)
    commissario = self.getCommissario()
    citta = model.Key("Citta", self.get_context().get("citta_key")).get()
    template_values["content"] = "map.html"
    template_values["limit"] = 100
    template_values["cittas"] = Citta.get_all()
    template_values["citta"] = citta
    template_values["centriCucina"] = CentroCucina.query().filter(CentroCucina.citta == citta.key).order(CentroCucina.nome)
    template_values['action'] = self.request.path
    self.getBase(template_values)
    
  
class ContattiHandler(BasePage):

  def get(self):
    template_values = dict()
    cm = None
    commissario = self.getCommissario(users.get_current_user())
    if self.request.get("cm") != "":
      cm = Commissione.get(self.request.get("cm"))
    elif commissario and commissario.commissione() :
      cm = commissario.commissione()

    if cm:
      template_values['commissari'] = cm.commissari()
    template_values["content"] = "contatti.html"
    self.getBase(template_values)

  _contacts_lock = threading.RLock()
  _contacts = None
  @classmethod
  def get_contacts(cls, num=20):
    if not cls._contacts:
      with cls._contacts_lock:     
        cls._contacts = list()
        i = 0
        for c in Commissario.get_all().order(-Commissario.creato_il):
          i +=1
          cls._contacts.append(c)
          if i >= num:
            break
    return cls._contacts
    
config = {
    'webapp2_extras.sessions': {
        'secret_key': 'wIDjEesObzp5nonpRHDzSp40aba7STuqC6ZRY'
    },
    'webapp2_extras.auth': {
        #        'user_model': 'models.User',
        'user_attributes': ['displayName', 'email'],
        },
    'webapp2_extras.jinja2': {
        'filters': {
            'do_pprint': do_pprint,
            },
        },
    }
    
app = webapp.WSGIApplication([
  ('/contatti', ContattiHandler),
  ('/commissioni', CommissioniHandler)
  ], debug=os.environ['HTTP_HOST'].startswith('localhost'), config=config)

def main():
  app.run();

if __name__ == "__main__":
  main()
