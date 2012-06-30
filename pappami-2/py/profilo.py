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

from google.appengine.ext.ndb import model
import webapp2 as webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

from gviz_api import *
from model import *
from form import CommissarioForm
from base import BasePage, CMCommissioniDataHandler, user_required, config, handle_404, handle_500

class CMProfiloHandler(BasePage):
  
  @user_required
  def get(self):
    commissario = self.getCommissario()
    form = CommissarioForm(obj=commissario)
    form.email = commissario.usera.get().email
    template_values = {
      'content': 'profilo.html',
      'cmsro': commissario,
      'form': form,
      'citta': Citta.get_all()      
    }
    self.getBase(template_values)
    
  @user_required
  def post(self):
    commissario = self.getCommissario()
    if(commissario):
      form = CommissarioForm(self.request.POST, commissario)
      form.populate_obj(commissario)
      form.citta = model.Key("Citta", int(self.request.get("citta")))

      privacy = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
      for what in range(0,len(privacy)):
        for who in range(0,len(privacy[0])):
          if self.request.get("p_"+str(what)+"_"+str(who)):
            privacy[what][who] = int(self.request.get("p_"+str(what)+"_"+str(who)))

      notify = [0,0,0]
      for what in range(0,len(notify)):
        if self.request.get("n_"+str(what)):
          notify[what] = int(self.request.get("n_"+str(what)))
          
      commissario.privacy = privacy
      commissario.notify = notify
      commissario.put()
      commissario.set_cache()
          
      old = list()
      for cm in commissario.commissioni():
        old.append(cm.key)
        #logging.info("old " + cc.commissione.nome)
      old = set(old)

      new = list()
      for c_key in self.request.get_all("commissione"):
        new.append(model.Key("Commissione", int(c_key)))
      new = set(new)

      todel = old - new
      toadd = new - old

      for cm_key in todel:
        commissione = cm_key.get()
        commissario.unregister(commissione)
        if commissione.calendario :
          pass
          #calendario = Calendario();        
          #calendario.logon(user=Configurazione.get_value_by_name("calendar_user"), password=Configurazione.get_value_by_name("calendar_password"))
          #calendario.load(commissione.calendario)
          #calendario.unShare(commissario.user.email())
        
      for cm_key in toadd:
        commissione = cm_key.get()
        commissario.register(commissione)
        if commissione.calendario :
          pass
          #calendario = Calendario();        
          #calendario.logon(user=Configurazione.get_value_by_name("calendar_user"), password=Configurazione.get_value_by_name("calendar_password"))
          #calendario.load(cc.commissione.calendario)
          #calendario.share(commissario.user.email())

      commissario.setCMDefault()
        
    self.response.out.write("Dati salvati.")

class CMAvatarHandler(BasePage):
      
  def post(self):
    cmd = self.request.get("cmd")
    #logging.info("cmd:" + cmd)
    if cmd == "upload":
      commissario = self.getCommissario()
      avatar_file = self.request.get("avatar_file")
      if avatar_file:
        if len(avatar_file) < 1000000 :
          avatar = images.resize(self.request.get("avatar_file"), 128,128)
          #logging.info(commissario.avatar_data)
          commissario.avatar_data = avatar
          logging.info("len: " + str(len(commissario.avatar_data)))
          #logging.info(commissario.avatar_data)          
          commissario.avatar_url = "/public/avatar?id="+str(commissario.usera.id())
          commissario.put()
          commissario.set_cache()
          self.response.out.write(commissario.avatar(cmsro=None,myself=True));
        else:
          logging.info("attachment is too big.")
    if cmd == "getimage":
      commissario = self.getCommissario()
      profile = commissario.usera.get().get_profile_by_strategy(self.request.get("provider"))
      if profile:
        user_info = profile.user_info.get("info")
        if user_info.get("image"):
          commissario.avatar_url=user_info.get("image").get("url")

      commissario.put()
      commissario.set_cache()
      self.response.out.write(commissario.avatar(cmsro=None,myself=True));
      
    
app = webapp.WSGIApplication([
    ('/profilo', CMProfiloHandler),
    ('/profilo/avatar', CMAvatarHandler),
    ('/profilo/getcm', CMCommissioniDataHandler)],
    debug = os.environ['HTTP_HOST'].startswith('localhost'), config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500

def main():
  app.run();

if __name__ == "__main__":
  main()