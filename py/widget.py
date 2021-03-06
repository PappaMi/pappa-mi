#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from py.base import *

import os
import cgi
import logging
from datetime import date, datetime, time, timedelta
import wsgiref.handlers

from google.appengine.ext.ndb import model
import webapp2 as webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import login_required

from py.model import *
from py.modelMsg import *

TIME_FORMAT = "T%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class CMMenuWidgetHandler(CMMenuHandler):

  def get(self):
    menu = Menu();

    bgcolor = self.request.get("bc")
    if(bgcolor is None):
      bgcolor = "eeeeff"
    fcolor = self.request.get("fc")
    if(fcolor is None):
      fcolor = "000000"

    template_values = dict()
    template_values["bgcolor"] = bgcolor
    template_values["fcolor"] = fcolor

    c = None
    if self.request.get("cm"):
      cmk = self.request.get("cm")
      cm_cache = Cache.get_cache('CMWidget')
      c = cm_cache.get(cmk)
      if not c:
        if cmk.isnumeric():
          c = model.Key("Commissione", int(self.request.get("cm"))).get()
        else:
          c = model.Key("Commissione", model.Key(urlsafe=self.request.get("cm")).id()).get()
          self.request.GET["cm"] = c.key.id()
        cm_cache.put(cmk, c)

      self.createMenu(self.request, c, template_values)
  
      template_values["main"] = 'widget/wmenu.html'
      self.getBase(template_values)
    else:
      self.response.out.write("commissione non trovata.")


class CMStatWidgetHandler(BasePage):

  def get(self):

    bgcolor = self.request.get("bc")
    if(bgcolor == ""):
      bgcolor = "eeeeff"
    fcolor = self.request.get("fc")
    if(fcolor == ""):
      fcolor = "000000"

    template_values = dict()
    template_values["bgcolor"] = bgcolor
    template_values["fcolor"] = fcolor

    c = None
    if self.request.get("cm"):
      cmk = self.request.get("cm")
      cm_cache = Cache.get_cache('CMWidget')
      c = cm_cache.get(cmk)
      if not c:
        if cmk.isnumeric():
          c = model.Key("Commissione", int(self.request.get("cm"))).get()
        else:
          c = model.Key("Commissione", model.Key(urlsafe=self.request.get("cm")).id()).get()
          self.request.GET["cm"] = c.key.id()
        cm_cache.put(cmk, c)

    self.createStat(self.request,c,template_values)

    t = ""
    if self.request.get("t") == "c":
      t = "_" + self.request.get("t")

    template_values["wcontent"] = "widget/stat" + t + ".html"

    if self.request.get("i") == "n":
      template_values["main"] = 'widget/' + template_values["wcontent"]
    else:
      template_values["main"] = 'widget/wstat.html'

    self.getBase(template_values)

  def createStat(self,request,c,template_values):

    now = datetime.now().date()
    year = now.year
    if now.month <= 9: #siamo in inverno -estate, data inizio = settembre anno precedente
      year = year - 1

    statCY = None
    statCC = None
    statCM = None
    if c:
      statCY = memcache.get("statCY" + str(c.citta.id))
      if not statCY:
        #logging.info("statCY miss")
        statCY = StatisticheIspezioni.get_cy_cc_cm_time(cy=c.citta, timeId=year).get()
        memcache.set("statCY" + str(c.citta.id), statCY, 86400)

      if c.getCentroCucina():
        cc_key = c.getCentroCucina().key
        statCC = memcache.get("statCC" + str(c.getCentroCucina().key.id))
        if not statCC:
          #logging.info("statCC miss")
          statCC = StatisticheIspezioni.get_cy_cc_cm_time(cc=cc_key, timeId=year).get()
          memcache.set("statCC" + str(cc_key.id), statCC, 86400)

      statCM = memcache.get("statCM" + str(c.key.id))
      if not statCM:
        #logging.info("statCM miss")
        statCM = StatisticheIspezioni.get_cy_cc_cm_time(cm=c.key, timeId=year).get()
        memcache.set("statCM" + str(c.key.id), statCM, 86400)

    template_values["statCY"] = statCY
    template_values["statCC"] = statCC
    template_values["statCM"] = statCM

class WidgetListitem:
  item = None
  date = None
  def __init__(self,item,date):
    self.item=item
    self.date=date

  def scuola(self):
    return self.item.commissione.tipoScuola + " " + self.item.commissione.nome

  def tipo(self):
    if isinstance(self.item, Ispezione):
      return "Ispezione"
    if isinstance(self.item, Nonconformita):
      return "Non Conformit&agrave;"
    if isinstance(self.item, Dieta):
      return "Ispezione Diete speciali"
    if isinstance(self.item, Nota):
      return "Note"
    return ""

  def date(self):
    if isinstance(self.item, Ispezione):
      return self.item.dataIspezione
    if isinstance(self.item, Nonconformita):
      return self.item.dataNonconf
    if isinstance(self.item, Dieta):
      return self.item.dataIspezione
    if isinstance(self.item, Nota):
      return self.item.dataNota

  def sommario(self):
      return self.item.sommario()

  def url(self):
    u = "#"
    post = SocialPost.get_by_resource(self.item.key)
    if len(post) and post[0] > 0:
      u = "/post/"+post[0].id
    else:
      logging.error("invalid item: " + str(self.item.key))
      
    return u


class CMListWidgetHandler(BasePage):

  def get(self):
    template_values = dict()

    bgcolor = self.request.get("bc")
    if(bgcolor is None):
      bgcolor = "eeeeff"
    fcolor = self.request.get("fc")
    if(fcolor is None):
      fcolor = "000000"

    template_values["bgcolor"] = bgcolor
    template_values["fcolor"] = fcolor

    items=list()
    c = None
    if self.request.get("cm"):
      cmk = self.request.get("cm")
      cm_cache = Cache.get_cache('CMWidget')
      c = cm_cache.get(cmk)
      if not c:
        if cmk.isnumeric():
          c = model.Key("Commissione", int(self.request.get("cm"))).get()
        else:
          c = model.Key("Commissione", model.Key(urlsafe=self.request.get("cm")).id()).get()
        cm_cache.put(cmk, c)

      items = memcache.get('widget-list-'+str(c.key.id()))
      if not items:
        items = list()
        limit = 20
        isps = Ispezione.get_by_cm(c.key, limit)
        for isp in isps:
          items.append(WidgetListitem(item=isp, date=isp.dataIspezione))
  
        ncs = Nonconformita.get_by_cm(c.key, limit)
        for nc in ncs:
          items.append(WidgetListitem(item=nc, date=nc.dataNonconf))
  
        diete = Dieta.get_by_cm(c.key)
        for dieta in diete:
          items.append(WidgetListitem(item=dieta, date=dieta.dataIspezione))
  
        note = Nota.get_by_cm(c.key, limit)
        for nota in note:
          items.append(WidgetListitem(item=nota, date=nota.dataNota))
  
        items = sorted(items, key=lambda item: item.date, reverse=True)
        memcache.set('widget-list-'+str(c.key.id()), items, 7200)

      template_values["host"] = self.getHost()
      template_values["items"] = items
      template_values["scuola"] = c.desc()
  
      template_values["main"] = 'widget/list.html'
  
      self.getBase(template_values)
    else:
      self.response.out.write("commissione non trovata.")      
      

class NodeWidgetHandler(BasePage):

  def get(self, node_key):
    if self.request.get("cmd") == "get_by_cm":
      try:
        node_key = SocialNode.get_by_resource(model.Key("Commissione", int(self.request.get("cm"))))[0].key
        self.output_as_json({'node_key': node_key.urlsafe()})
      except:
        #logging.info("error retrieving node: " + self.request.get("cm"))
        return
    elif node_key:
      template_values = dict()

      bgcolor = self.request.get("bc")
      if(bgcolor is None):
        bgcolor = "eeeeff"
      fcolor = self.request.get("fc")
      if(fcolor is None):
        fcolor = "000000"

      template_values["bgcolor"] = bgcolor
      template_values["fcolor"] = fcolor

      template_values["node_key"] = node_key
      template_values["main"] = 'widget/node.html'

      self.getBase(template_values)

class CMGadgetHandler(BasePage):

  def get(self):
    nodes = memcache.get('gadget_nodes')
    if not nodes:
      nodes = SocialNode.query().order(SocialNode.name).fetch()
      memcache.set('gadget_nodes', nodes)
    template_values = dict()
    template_values["main"] = "widget/gadget.xml"
    template_values["host"] = self.getHost()
    template_values["nodes"] = nodes
    self.getBase(template_values)


class CMWidgetHandler(BasePage):

  def get(self):
    template_values = dict()
    template_values["content"] = "widget/widgetindex.html"
    template_values["host"] = self.getHost()
    template_values["citta"] = Citta.get_all()
    self.getBase(template_values)

app = webapp.WSGIApplication([
  ('/widget/get', CMWidgetHandler),
  ('/widget/menu', CMMenuWidgetHandler),
  ('/widget/stat', CMStatWidgetHandler),
  ('/widget/list', CMListWidgetHandler),
  ('/widget/node/(.*)', NodeWidgetHandler),
  ('/widget/node(.*)', NodeWidgetHandler),
  ('/widget/gadget', CMGadgetHandler),
  ('/widget/getcm', CMCommissioniDataHandler)
  ], debug = os.environ['HTTP_HOST'].startswith('localhost'), config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500
