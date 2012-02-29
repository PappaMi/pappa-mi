#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
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

from py.base import BasePage, CMMenuHandler, Const, ActivityFilter, commissario_required, user_required
import cgi, logging, os
from datetime import date, datetime, time, timedelta
import wsgiref.handlers
import fixpath

from google.appengine.ext.ndb import model
from google.appengine.api import users
import webapp2 as webapp
from google.appengine.api import memcache

from py.model import *
from py.modelMsg import *
from py.comments import *

class CMMenuDataHandler(CMMenuHandler):
  
  def get(self): 
    if( self.request.get("cmd") == "getbydate" ):
      menu = Menu();
      data = datetime.strptime(self.request.get("data"),Const.DATE_FORMAT).date()
      c = model.Key("Commissione", int(self.request.get("commissione"))).get()
      menu = self.getMenu(data, c)[0]
      
      json.dump(menu.to_dict(), self.response.out)
      logging.info(json.dumps(menu.to_dict()))

    else:
      template_values = dict()
      template_values['content'] = 'menu.html'      
      template_values["citta"] = Citta.get_all()
      self.getBase(template_values)

  def post(self):
    cm_key = self.get_context().get("cm_key")
    if cm_key:
      cm = model.Key("Commissione", cm_key).get()
    if self.request.get("cm"):
      cm = model.Key("Commissione", int(self.request.get("cm"))).get()
    
    template_values = dict()
    template_values['content'] = 'menu.html'      
    template_values["citta"] = Citta.get_all()

    if cm:
      self.get_context()["citta_key"] = cm.citta.id()
      self.get_context()["cm_key"] = cm.key.id()
      self.get_context()["cm_name"] = cm.desc()    
    
    self.getBase(template_values)
    
      

class CMMenuSlideHandler(CMMenuHandler):
  
  def get(self): 
    template_values = dict()
    template_values['main'] = 'menu_slides.html'    
    self.getBase(template_values)

config = {
    'webapp2_extras.sessions': {
        'secret_key': 'wIDjEesObzp5nonpRHDzSp40aba7STuqC6ZRY'
    },
    'webapp2_extras.auth': {
        #        'user_model': 'models.User',
        'user_attributes': ['displayName', 'email'],
        },
    }
    
app = webapp.WSGIApplication([
  ('/menu', CMMenuDataHandler),
  ('/menuslide', CMMenuSlideHandler)
  ], debug=os.environ['HTTP_HOST'].startswith('localhost'), config=config)

def main():
  app.run();

if __name__ == "__main__":
  main()
    