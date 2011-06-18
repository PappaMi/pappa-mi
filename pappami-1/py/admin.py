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

import os
import cgi
import logging
import urllib
from google.appengine.api import urlfetch
from datetime import datetime, date, time
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

from py.model import *
from py.form import CommissioneForm
from py.gviz_api import *
from py.base import BasePage
from py.calendar import *

TIME_FORMAT = "T%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class CMAdminMenuHandler(BasePage):

  def get(self):    

    template_values = {
      'content_left': 'admin/leftbar.html',
      'content': 'admin/menu.html'
    }

    if( self.request.get("data") ):
      data = datetime.datetime.strptime(self.request.get("data"),DATE_FORMAT).date()
      menu = Menu.all().filter("validitaA >=", data).order("-validitaA").order("settimana").order("giorno")
      template_values['data'] = data
      template_values['menu'] = menu

    self.getBase(template_values)

  def post(self):    
    if( self.request.get("cmd") == "list" ):

      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()

      template_values = {
        'content_left': 'admin/leftbar.html',
        'content': 'admin/menu.html'
      }

      if self.request.get("data") :
        data = datetime.datetime.strptime(self.request.get("data"),DATE_FORMAT).date()
        menu = Menu.all().filter("validitaA >=", data).order("-validitaA").order("settimana").order("giorno")
        template_values['data'] = data
        template_values['menu'] = menu

      self.getBase(template_values)


class CMAdminCommissioneHandler(BasePage):

  def get(self):    

    if self.request.get("cmd") == "open":

      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()

      key = ""
      
      if(self.request.get("key") == ""):
        commissione = Commissione()       
      else:
        commissione = Commissione.get(self.request.get("key"))    
        key = commissione.key()
              
      template_values = {
        'content_left': 'admin/leftbar.html',
        'content': 'admin/commissione.html',
        'commissione': commissione,
        'key': key,
        'offset': self.request.get("offset"),
        'tipoScuola': self.request.get("tipoScuola"),
        'centroCucina': self.request.get("centroCucina"),
        'zona': self.request.get("zona"),
        'distretto': self.request.get("distretto"),
        'centriCucina': CentroCucina.all().order("nome")
      }
    
      self.getBase(template_values)

    else:
      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()

      centriCucina = CentroCucina.all().order("nome")

      template_values = {
        'content_left': 'admin/leftbar.html',
        'content': 'admin/commissioni.html',
        'centriCucina': centriCucina,
      }
      self.getBase(template_values)
      
      #if self.request.get("offset"):
        #offset = int(self.request.get("offset"))
      #else:
        #offset = 0
        
      #if offset > 0:
        #prev = offset - 10
      #else:
        #prev = None
      #next = offset + 10
      
      ## Creating the data
      #description = {"nome": ("string", "Commissione"),
                     #"nomeScuola": ("string", "Scuola"),
                     #"tipo": ("string", "Tipo"),
                     #"indirizzo": ("string", "Indirizzo"),
                     #"distretto": ("string", "Dist."),
                     #"zona": ("string", "Zona"),
                     #"geo": ("string", "Geo"),
                     #"comando": ("string", "")}
      
      #commissioni = Commissione.all()
      #if self.request.get("tipoScuola") :
        #commissioni = commissioni.filter("tipoScuola", self.request.get("tipoScuola"))
      #if self.request.get("centroCucina") :
        #commissioni = commissioni.filter("centroCucina", CentroCucina.get(self.request.get("centroCucina")))
      #if self.request.get("nome") :
        #commissioni = commissioni.filter("nome>=", self.request.get("nome"))
        #commissioni = commissioni.filter("nome<", self.request.get("nome") + u'\ufffd')

      #data = list()
      #try:
        #for commissione in commissioni.order("nome").fetch(10, offset):
          #data.append({"nome": commissione.nome, "nomeScuola": commissione.nomeScuola, "tipo": commissione.tipoScuola, "indirizzo": commissione.strada + ", " + commissione.civico + ", " + commissione.cap + " " + commissione.citta, "distretto": commissione.distretto, "zona": commissione.zona, "geo": str(commissione.geo != None), "comando":"<a href='/admin/commissione?cmd=open&key="+str(commissione.key())+"&offset="+str(offset)+ "&tipoScuola=" + self.request.get("tipoScuola") + "&centroCucina=" + self.request.get("centroCucina") + "&zona="+ self.request.get("zona") + "&distretto=" + self.request.get("distretto")+"'>Apri</a>"})
      #except db.Timeout:
        #errmsg = "Timeout"
        
      ## Loading it into gviz_api.DataTable
      #data_table = DataTable(description)
      #data_table.LoadData(data)

      ## Creating a JSon string
      #gvizdata = data_table.ToJSon(columns_order=("nome", "nomeScuola", "tipo", "indirizzo", "distretto", "zona", "geo", "comando"))

      #centriCucina = CentroCucina.all().order("nome")

      #template_values = {
        #'content_left': 'admin/leftbar.html',
        #'content': 'admin/commissioni.html',
        #'centriCucina': centriCucina,
        #'gvizdata': gvizdata,
        #'prev': prev,
        #'next': next,
        #'tipoScuola': self.request.get("tipoScuola"),
        #'centroCucina': self.request.get("centroCucina"),
        #'zona': self.request.get("zona"),
        #'distretto': self.request.get("distretto"),
        #'nome': self.request.get("nome")
      #}
      #self.getBase(template_values)

  def post(self):    
    if( self.request.get("cmd") == "save" ):
      if self.request.get("key"):
        commissione = Commissione.get(self.request.get("key"))
      else:
        commissione = Commissione()
        
      form = CommissioneForm(data=self.request.POST, instance=commissione)
      
      if form.is_valid():
        commissione = form.save(commit=False)
        commissione.geo = db.GeoPt(float(self.request.get("lat")), float(self.request.get("lon")))
        commissione.put()

      self.redirect("/admin/commissione?offset=" + self.request.get("offset") + "&tipoScuola=" + self.request.get("q_tipoScuola") + "&centroCucina=" + self.request.get("q_centroCucina") + "&zona="+ self.request.get("q_zona") + "&distretto=" + self.request.get("q_distretto") )
      
    elif self.request.get("cmd") == "list":
      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()
 
      centriCucina = CentroCucina.all().order("nome")
      
      #if query.is_valid():
      commissioni = Commissione.all()
      if self.request.get("tipoScuola") :
        commissioni = commissioni.filter("tipoScuola", self.request.get("tipoScuola"))
      if self.request.get("centroCucina") :
        commissioni = commissioni.filter("centroCucina", CentroCucina.get(self.request.get("centroCucina")))
      if self.request.get("nome") :
        commissioni = commissioni.filter("nome>=", self.request.get("nome"))
        commissioni = commissioni.filter("nome<", self.request.get("nome") + u'\ufffd')

      template_values = {
        'content_left': 'admin/leftbar.html',
        'content': 'admin/commissioni.html',
        'commissioni': commissioni,
        'centriCucina': centriCucina,
        'tipoScuola': self.request.get("tipoScuola"),
        'centroCucina': self.request.get("centroCucina"),
        'prev': self.requst.get("prev"),
        'next': self.requst.get("next"),
        'nome': self.request.get("nome")
      }
      self.getBase(template_values)

class CMAdminCommissioneDataHandler(BasePage):

  def get(self):    
      tq = urllib.unquote(self.request.get("tq"))
      #logging.info(tq)
      query = tq[:tq.find("limit")]
      #logging.info(query)
      
      orderby = "nome"
      if(query.find("by") > 0):
        orderby = query[query.find("`"):query.rfind("`")].strip("` ")
      if(query.find("desc") > 0):
        orderby = "-" + orderby

      tipoScuola = None;
      if(query.find("tipoScuola") >= 0):
        tipoScuola = query[(query.find("tipoScuola ") + len("tipoScuola ")):]
        tipoScuola = tipoScuola[:tipoScuola.find(" ")]

      centroCucina = None;
      if(query.find("centroCucina") >= 0):
        centroCucina = query[(query.find("centroCucina ") + len("centroCucina ")):]
        centroCucina = centroCucina[:centroCucina.find(" ")]
      
      #logging.info(orderby)
      
      params = tq[tq.find("limit"):].split()
      #logging.info(params)
      limit = int(params[1])
      offset = int(params[3])
      
      if params[3] >= 0:
        offset = int(params[3])
      else:
        offset = 0
        
      if offset > 0:
        prev = offset - 10
      else:
        prev = None
      next = offset + 10
      
      # Creating the data
      description = {"nome": ("string", "Commissione"),
                     "nomeScuola": ("string", "Scuola"),
                     "tipoScuola": ("string", "Tipo"),
                     "strada": ("string", "Indirizzo"),
                     "distretto": ("string", "Dist."),
                     "zona": ("string", "Zona"),
                     "geo": ("string", "Geo"),
                     "comando": ("string", "")}
      
      commissioni = Commissione.all()
      if tipoScuola :
        commissioni = commissioni.filter("tipoScuola", tipoScuola)
      if centroCucina :
        commissioni = commissioni.filter("centroCucina", CentroCucina.get(centroCucina))
      if self.request.get("nome") :
        commissioni = commissioni.filter("nome>=", self.request.get("nome"))
        commissioni = commissioni.filter("nome<", self.request.get("nome") + u'\ufffd')

      data = list()
      try:
        for commissione in commissioni.order(orderby).fetch(limit, offset):
          data.append({"nome": commissione.nome, "nomeScuola": commissione.nomeScuola, "tipoScuola": commissione.tipoScuola, "strada": commissione.strada + ", " + commissione.civico + ", " + commissione.cap + " " + commissione.citta, "distretto": commissione.distretto, "zona": commissione.zona, "geo": str(commissione.geo != None), "comando":"<a href='/admin/commissione?cmd=open&key="+str(commissione.key())+"&offset="+str(offset)+ "&tipoScuola=" + self.request.get("tipoScuola") + "&centroCucina=" + self.request.get("centroCucina") + "&zona="+ self.request.get("zona") + "&distretto=" + self.request.get("distretto")+"'>Apri</a>"})
      except db.Timeout:
        errmsg = "Timeout"
        
      # Loading it into gviz_api.DataTable
      data_table = DataTable(description)
      data_table.LoadData(data)

      # Creating a JSon string
      self.response.out.write("google.visualization.Query.setResponse({reqId: '0',status:'ok',table:" + data_table.ToJSon(columns_order=("nome", "nomeScuola", "tipoScuola", "strada", "distretto", "zona", "geo", "comando"))+",version: '0.6'})")
  
class CMAdminHandler(BasePage):

  def get(self):    

    if self.request.get("cmd") == "initConfig":
      dummy = Configurazione(nome="dummyname", valore="dummyvalue")
      dummy.put()
    
    if self.request.get("cmd") == "initAnno":
      d2008da = date(2008,9,1)
      d2008a = date(2009,7,31)
      d2009da = date(2009,9,1)
      d2009a = date(2010,7,31)
      d2010da = date(2010,9,1)
      d2010a = date(2011,7,31)
      for isp in Ispezione.all() :
        if isp.dataIspezione >= d2008da and isp.dataIspezione < d2008a :
          isp.anno = 2008
        if isp.dataIspezione >= d2009da and isp.dataIspezione < d2009a :
          isp.anno = 2009
        if isp.dataIspezione >= d2010da and isp.dataIspezione < d2010a :
          isp.anno = 2010
        isp.put()
      for nc in Nonconformita.all() :
        if nc.dataNonconf >= d2008da and nc.dataNonconf < d2008a :
          nc.anno = 2008
        if nc.dataNonconf >= d2009da and nc.dataNonconf < d2009a :
          nc.anno = 2009
        if nc.dataNonconf >= d2010da and nc.dataNonconf < d2010a :
          nc.anno = 2010
        nc.put()
          
    
    if self.request.get("cmd") == "initZone":
      for cc in CentroCucina.all():
        ccZona = CentroCucinaZona(centroCucina = cc, zona = cc.menuOffset + 1, validitaDa=date(year=2008,month=3, day=1), validitaA=date(year=2010,month=10, day=31))
        ccZona.put()
      for cm in Commissione.all():
        cmCC = CommissioneCentroCucina(commissione = cm, centroCucina = cm.centroCucina, validitaDa=date(year=2008,month=3, day=1), validitaA=date(year=2099,month=12, day=31))
        cmCC.put()
      for z in range(1,5):
        zonaOld = ZonaOffset(zona = z, offset = 4-z, validitaDa=date(year=2008,month=3, day=1), validitaA=date(year=2010,month=10, day=31))
        zonaOld.put()
        zona = ZonaOffset(zona = z, offset = 4-z, validitaDa=date(year=2010,month=11, day=1), validitaA=date(year=2099,month=12, day=31))
        zona.put()
        
    if self.request.get("cmd") == "getCommissari":
      buff = "Name,Given Name,Additional Name,Family Name,Yomi Name,Given Name Yomi,Additional Name Yomi,Family Name Yomi,Name Prefix,Name Suffix,Initials,Nickname,Short Name,Maiden Name,Birthday,Gender,Location,Billing Information,Directory Server,Mileage,Occupation,Hobby,Sensitivity,Priority,Subject,Notes,Group Membership,E-mail 1 - Type,E-mail 1 - Value\r"
      for c in Commissario.all():
        if c.isCommissario():
          buff = buff + c.nome + " " + c.cognome + "," + c.nome + ",," + c.cognome + ",,,,,,,,,,,,,,,,,,,,,,,Commissari attivi Pappa-Mi ::: * My Contacts,* ," + c.user.email() + "\r"
        
      self.response.out.write(buff)        
      return

    if self.request.get("cmd") == "getGenitori":
      buff = "Name,Given Name,Additional Name,Family Name,Yomi Name,Given Name Yomi,Additional Name Yomi,Family Name Yomi,Name Prefix,Name Suffix,Initials,Nickname,Short Name,Maiden Name,Birthday,Gender,Location,Billing Information,Directory Server,Mileage,Occupation,Hobby,Sensitivity,Priority,Subject,Notes,Group Membership,E-mail 1 - Type,E-mail 1 - Value\r"
      for c in Commissario.all():
        if c.isGenitore():
          buff = buff + c.nome + " " + c.cognome + "," + c.nome + ",," + c.cognome + ",,,,,,,,,,,,,,,,,,,,,,,Genitori attivi Pappa-Mi ::: * My Contacts,* ," + c.user.email() + "\r"
        
      self.response.out.write(buff)
      return
      
    
    if self.request.get("cmd") == "flush":
      memcache.flush_all()

    if self.request.get("cmd") == "flushnews":
      #url = "http://groups.google.com/group/pappami-aggiornamenti/feed/atom_v1_0_msgs.xml"
      #result = urlfetch.fetch(url)
      #if result.status_code == 200:
        #logging.info("ok")
        #logging.info(result.content)
      #else:
        #logging.info("error")
        #logging.info(result.status_code)
        #logging.info(result.content)
      memcache.delete("news_pappami")
      memcache.delete("news_web")
      memcache.delete("news_cal")

    if self.request.get("cmd") == "offset":
      ccs = CentroCucina.all()
      for cc in ccs:
        if cc.menuOffset == None:
          cc.menuOffset = None
          cc.put()
      
    template_values = {
      'content_left': 'admin/leftbar.html',
      'content': ''
    }
    self.getBase(template_values)

class CMAdminCommissarioHandler(BasePage):

  def get(self):    

    if( self.request.get("cmd") == "enable" or
        self.request.get("cmd") == "disable" ):
      
      commissario = Commissario.get(self.request.get("key"))

      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()

      calendario = Calendario()
      calendario.logon(user=Configurazione.all().filter("nome","calendar_user").get().valore, password=Configurazione.all().filter("nome", "calendar_password").get().valore)
      
      if self.request.get("cmd") == "enable":
        if commissario.isRegCommissario():
          commissario.stato = 1
          for c in commissario.commissioni():
            c.numCommissari = c.numCommissari + 1
            c.put() 

            if(c.calendario):
              calendario.load(c.calendario)
              calendario.share(commissario.user.email())
            
        else:
          commissario.stato = 11
      elif self.request.get("cmd") == "disable" : 
        if commissario.isCommissario():
          commissario.stato = 0 
          for c in commissario.commissioni():
            c.numCommissari = c.numCommissari - 1
            c.put() 
        else:
          commissario.stato = 10
        
      commissario.put()
      memcache.set("commissario" + str(user.user_id()), commissario, 600)
      
     
      if commissario.stato == 1:              
        
        host = self.getHost()
        
        sender = "Pappa-Mi <aiuto@pappa-mi.it>"
        message = mail.EmailMessage()
        message.sender = sender
        message.to = commissario.user.email()
        message.bcc = sender
        message.subject = "Benvenuto in Pappa-Mi"
        message.body = """ La tua richiesta di registrazione come Commissario e' stata confermata.
        
        Ora puoi accedere all'applicazione utilizzando il seguente link:
        
        http://"""  + host + """/commissario
        
        e iniziare a inserire le schede di valutazione e di non conformita'
        
        Ciao
        Pappa-Mi staff
        
        """
          
        message.send()
        
        memcache.delete("markers")
        memcache.delete("markers_all")
        memcache.delete("stats")
      
      self.redirect("/admin/commissario")
    
    else:
      url = users.create_logout_url("/")
      url_linktext = 'Logout'
      user = users.get_current_user()

      # Creating the data
      description = {"nome": ("string", "Nome"),
                     "cognome": ("string", "Cognome"),
                     "email": ("string", "Email"),
                     "commissioni": ("string", "Commissioni"),
                     "stato": ("string", "Stato"),
                     "ultimo_accesso_il": ("string", "Ultimo accesso"),
                     "comando": ("string", "Azione")}
      
      data = list()
      for commissario in Commissario.all():
        if commissario.isRegCommissario():
          stato = "Richiesta"
          comando = "Attiva"
          cmd = "enable"
        elif commissario.isCommissario():
          stato = "Commissario"
          comando = "Disabilita"
          cmd = "disable"
        elif commissario.isGenitore():
          stato = "Genitore"
          comando = "Disabilita"
          cmd = "disable"
        
        commissioni = ""
        for c in commissario.commissioni():
          commissioni = commissioni + c.nome + " - " + c.tipoScuola + "<br/>"

        data.append({"nome": commissario.nome, "cognome": commissario.cognome, "email": commissario.user.email(), "commissioni": commissioni, "stato":stato, "ultimo_accesso_il":commissario.ultimo_accesso_il, "comando":"<a href='/admin/commissario?cmd="+cmd+"&key="+str(commissario.key())+"'>"+comando+"</a>"})

      # Loading it into gviz_api.DataTable
      data_table = DataTable(description)
      data_table.LoadData(data)

      # Creating a JSon string
      json = data_table.ToJSon(columns_order=("nome", "cognome", "email", "commissioni", "stato", "ultimo_accesso_il", "comando"), order_by="cognome")

 
      template_values = {
        'content_left': 'admin/leftbar.html',
        'content': 'admin/commissari.html',
        'json': json
      }
      self.getBase(template_values)
        
def main():
  debug = os.environ['HTTP_HOST'].startswith('localhost')   

  application = webapp.WSGIApplication([
  ('/admin/commissione', CMAdminCommissioneHandler),
  ('/admin/commissione/getdata', CMAdminCommissioneDataHandler),
  ('/admin/menu', CMAdminMenuHandler),
  ('/admin/commissario', CMAdminCommissarioHandler),
  ('/admin', CMAdminHandler)
  ], debug=debug)

  wsgiref.handlers.CGIHandler().run(application)
  
if __name__ == "__main__":
  main()