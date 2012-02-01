#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from py.base import *

import os
import cgi
import logging
import urllib
from datetime import date, datetime, time, timedelta
import wsgiref.handlers

from ndb import model
from google.appengine.api import users
import webapp2 as webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

from gviz_api import *
from model import *
from form import CommissarioForm
from base import BasePage, CMCommissioniDataHandler, user_required
from gcalendar import *

class CMProfiloHandler(BasePage):
  
  @user_required
  def get(self):
    user = users.get_current_user()
    commissario = self.getCommissario(users.get_current_user())
    template_values = {
      'content': 'profilo.html',
      'cmsro': commissario,
      'citta': Citta.all().order("nome")      
    }
    self.getBase(template_values)
    
  @user_required
  def post(self):
    user = users.get_current_user()
    commissario = self.getCommissario(users.get_current_user())
    if(commissario):
      form = CommissarioForm(self.request.POST, commissario)
      form.populate_obj(commissario)
      commissario.put()

      old = list()
      for cc in CommissioneCommissario.all().filter("commissario",commissario):
        old.append(str(cc.commissione.key()))
        #logging.info("old " + cc.commissione.nome)
      old = set(old)

      new = list()
      for c_key in self.request.get_all("commissione"):
        new.append(c_key)
        logging.info("new " + Commissione.get(model.Key(c_key)).nome)
      new = set(new)

      todel = old - new
      toadd = new - old

      for cm in todel:
        commissione = Commissione.get(cm)
        commissario.unregister(cm)
        if commissione.calendario :
          calendario = Calendario();        
          calendario.logon(user=Configurazione.get_value_by_name("calendar_user"), password=Configurazione.get_value_by_name("calendar_password"))
          calendario.load(commissione.calendario)
          calendario.unShare(commissario.user.email())
        
      for cm in toadd:
        commissione = Commissione.get(cm)
        commissario.register(cm)
        if cc.commissione.calendario :
          calendario = Calendario();        
          calendario.logon(user=Configurazione.get_value_by_name("calendar_user"), password=Configurazione.get_value_by_name("calendar_password"))
          calendario.load(cc.commissione.calendario)
          calendario.share(commissario.user.email())

      commissario.setCMDefault()
        
    self.response.out.write("Dati salvati.")

class CMAvatarHandler(BasePage):
      
  def post(self):
    cmd = self.request.get("cmd")
    logging.info("cmd:" + cmd)
    if cmd == "upload":
      commissario = self.getCommissario(users.get_current_user())
      avatar_file = self.request.get("avatar_file")
      logging.info("1")
      if avatar_file:
        if len(avatar_file) < 1000000 :
          logging.info("2")
          avatar = images.resize(self.request.get("avatar_file"), 128,128)
          commissario.avatar_data = avatar
          commissario.avatar_url = "/public/avatar?key=" + str(commissario.key())
          commissario.put()
          self.response.out.write(commissario.avatar()+"&size=big");
        else:
          logging.info("attachment is too big.")
    if cmd == "saveurl":
      commissario = self.getCommissario(users.get_current_user())
      commissario.avatar_url = self.request.get("picture")
      commissario.put()
    
app = webapp.WSGIApplication([
    ('/profilo', CMProfiloHandler),
    ('/profilo/avatar', CMAvatarHandler),
    ('/profilo/getcm', CMCommissioniDataHandler)],
    debug = os.environ['HTTP_HOST'].startswith('localhost'))

def main():
  app.run();

if __name__ == "__main__":
  main()