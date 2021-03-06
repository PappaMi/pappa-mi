#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Pappa-Mi org
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
#

from py.base import BasePage, CMMenuHandler, Const, commissario_required, user_required, config, handle_404, handle_500
import cgi, logging, os
from datetime import date, datetime, time, timedelta
import wsgiref.handlers
import fixpath
from google.appengine.api import urlfetch
from HTMLParser import HTMLParser

from google.appengine.ext.ndb import model
from google.appengine.api import users
import webapp2 as webapp
from google.appengine.api import memcache

from py.model import *
import py.PyRSS2Gen

class CMMenuDataHandler(CMMenuHandler):

  def get(self):
    if( self.request.get("cmd") == "getbydate" ):
      menu = Menu();
      data = datetime.strptime(self.request.get("data"),Const.DATE_FORMAT).date()
      c = model.Key("Commissione", int(self.request.get("commissione"))).get()
      menus = self.getMenu(data, c)
      if len(menus):
        menu = self.getMenu(data, c)[0]

      json.dump(menu.to_dict(), self.response.out)

    elif( self.request.get("cmd") == "getdetails" ):
      details = dict()
      factors = {'Materna': 0.625,
                 'Primaria': 0.875,
                 'Secondaria': 1.0}
      factor = 1.0
      if self.request.get('cm'):
        cm = model.Key('Commissione', int(self.request.get('cm'))).get()
        factor = factors[cm.tipoScuola]
      piatto_key = model.Key("Piatto", int(self.request.get("piatto")))
      details['piatto'] = piatto_key.get().nome
      details['ingredienti'] = list()

      for p_i in PiattoIngrediente.query().filter(PiattoIngrediente.piatto==piatto_key):
        ing = p_i.ingrediente.get()
        qty = p_i.quantita
        details['ingredienti'].append({'nome': ing.nome,
                                       'quantita': p_i.quantita * factor})

      details['ingredienti'].sort(key=lambda item: item.get('quantita'), reverse=True)
      json.dump(details, self.response.out)

    elif( self.request.get("format") == "rss" ):
      menu = Menu();
      data = datetime.now().date()
      data = self.get_next_working_day(data)

      c = model.Key("Commissione", int(self.request.get("cm"))).get()
      menus = self.getMenu(data, c)
      items = list()

      for menu in menus:

        items.append(py.PyRSS2Gen.RSSItem(title = menu.getData(),
                          description = "Primo: " + menu.primo.nome + " - Secondo: " + menu.secondo.nome + " - Contorno: " + menu.contorno.nome + " - Dessert: " + menu.dessert.nome,
                          guid = py.PyRSS2Gen.Guid("http://" + self.getHost() + "/menu?cm=" + str(c.key.id())),
                          link = "http://" + self.getHost() + "/menu?cm=" + str(c.key.id()),
                          pubDate = menu.data.strftime("%a, %d %b %Y %H:%M:%S +0100")))


      rss = py.PyRSS2Gen.RSS2( title = "Pappa-Mi - " + c.nome,
                               link = "http://" + self.getHost() + "/menu?cm=" + str(c.key.id()),
                               description = "Menu' per la Scuola " + c.nome,
                               items = items)

      expires_date = datetime.utcnow() + timedelta(1)
      expires_str = expires_date.strftime("%d %b %Y %H:%M:%S GMT")
      self.response.headers.add_header("Expires", expires_str)
      self.response.out.write(rss.to_xml())
    else:
      template_values = dict()
      template_values['content'] = 'menu.html'
      template_values["todayofweek"] = self.get_next_working_day(datetime.now().date()).isoweekday()
      template_values["cittas"] = Citta.get_all()

      self.getBase(template_values)

  def post(self):
    cm_key = self.get_context().get("cm_key")
    cm = None
    if cm_key:
      cm = model.Key("Commissione", cm_key).get()
    if self.request.get("cm"):
      logging.info(self.request.get("cm"))
      cm = model.Key("Commissione", int(self.request.get("cm"))).get()

    template_values = dict()
    template_values['content'] = 'menu.html'
    template_values["cittas"] = Citta.get_all()
    template_values["todayofweek"] = self.get_next_working_day(datetime.now().date()).isoweekday()

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

  def getBase(self,template_values):
    cm = None

    if self.get_context().get("cm_key"):
      cm = model.Key("Commissione", self.get_context()["cm_key"]).get()

    if not cm:
      commissario = self.getCommissario(self.get_current_user())
      if self.request.get("cm") != "":
        cm = model.Key("Commissione",int(self.request.get("cm"))).get()
      elif commissario and commissario.commissione() :
        cm = commissario.commissione()
      else:
        if commissario and commissario.citta:
          cm = Commissione.get_by_citta(commissario.citta)[0]

    if cm:
      date = self.request.get("data")
      if date:
        date = datetime.strptime(date,Const.DATE_FORMAT).date()
      else:
        date = datetime.now().date()

      date = self.get_next_working_day(date)

      date1 = date - timedelta(date.isoweekday() - 1)
      datep = date1 - timedelta(7)
      daten = date1 + timedelta(7)

      template_values['menu'] = self.getMenuWeek(date1, cm)
      template_values['data'] = date
      template_values['data1'] = date1
      template_values['datap'] = datep
      template_values['datan'] = daten
      template_values['cm'] = cm

    template_values['action'] = self.request.path
    super(CMMenuHandler,self).getBase(template_values)


class MenuScraper(BasePage):

  def get(self):
    template_values = dict()

    year = int(self.request.get('y'))
    month = int(self.request.get('m'))
    day = int(self.request.get('d'))

    menutext = ""
    d_start = date(year=year, month=month, day=day)
    for i in range(0, 28):
        d = d_start + timedelta(days=i)
        if d.isoweekday() < 6:
            response = urlfetch.fetch('http://www.milanoristorazione.it/modules/mod_cosasimangia/views/new/newmenu.php?codRefe=000413&x1='+str(d.day)+'&x2='+str(d.month)+'&x3='+str(d.year), deadline=60)
            p = MenuParser()
            p.text = ""
            p.feed(response.content)
            d_end = date(2099, 12, 31)
            d_week = i / 7 + 1
            menutext += "Materna" + str("\t") + d_start.strftime("%d/%m/%Y") + "\t" + d_end.strftime("%d/%m/%Y") + "\t" + str(d_week) + "\t" + str(d.isoweekday()) + "\t" + str(p.text) + "\n"

    self.response.out.write(menutext)


# create a subclass and override the handler methods
class MenuParser(HTMLParser):


  piatti = set()
  settimane = list()

  curr_id = ""
  def handle_starttag(self, tag, attrs):
    for attrid, attrvalue in attrs:
      if attrid == "id":
        self.curr_id=attrvalue

  def handle_endtag(self, tag):
    pass

  def handle_data(self, data):
    #logging.info(data)
    if self.curr_id == "divdayright":
      logging.info(data)
      self.text += data + "\t"
      self.curr_id=""


app = webapp.WSGIApplication([
  ('/menu', CMMenuDataHandler),
  ('/menuslide', CMMenuSlideHandler),
  ('/menu/scrape', MenuScraper),
  ], debug=os.environ['HTTP_HOST'].startswith('localhost'), config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
