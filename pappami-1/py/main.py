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

from py.base import BasePage, CMMenuHandler
import os
import cgi
import logging
from datetime import date, datetime, time, timedelta
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
import py.feedparser

from py.widget import CMMenuWidgetHandler, CMStatWidgetHandler
from google.appengine.dist import use_library 

from py.model import *

TIME_FORMAT = "T%H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

  
class MainPage(BasePage):

  _news = {"news_pappami":"http://blog.pappa-mi.it/feeds/posts/default",
          "news_web": "http://www.google.com/reader/public/atom/user%2F14946287599631859889%2Fstate%2Fcom.google%2Fbroadcast",
          "news_cal": "http://www.google.com/calendar/feeds/aiuto%40pappa-mi.it/public/basic"}
  def getNews(self,name):
    news = memcache.get(name)
    i = 0
    if news is None:
      news_all = py.feedparser.parse(self._news[name])
      #logging.debug(news_all)
      news = []
      for n in news_all.entries:
        #logging.debug(n)
        if i >= 4 :
          break
        i = i + 1
        news.append(n)
        
      memcache.add(name,news)
    return news
  
  def get(self):
    template_values = dict()
    template_values["content"] = "public.html"
    template_values["billboard"] = "billboard.html"
    template_values["content_left"] = "leftbar.html"
    template_values["content_right"] = "rightbar.html"
    template_values["content_extra"] = "extra.html"
    template_values["host"] = self.getHost()
  
    stats = self.getStats()

    c = None
    commissario = self.getCommissario(users.get_current_user())
    if commissario:
      c = commissario.commissione()
    
    CMMenuWidgetHandler().createMenu(self.request,c,template_values)
    CMStatWidgetHandler().createStat(self.request,c,template_values)
    template_values["bgcolor"] = "eeeeff"
    template_values["fgcolor"] = "000000"
    
    template_values["stat"] = stats
    template_values["news_pappami"] = self.getNews("news_pappami")
    template_values["news_pappami_alt"] = "http://blog.pappa-mi.it/"
    #template_values["news_web"] = self.getNews("news_web")
    #template_values["news_cal"] = self.getNews("news_cal")

    #if(len(self.getNews("news_pappami"))>0):
    #  template_values["newsMsg"] = self.getNews("news_pappami")[0].content[0]

    self.getBase(template_values)

  def getStats(self):
    stats = memcache.get("stats")
    if(stats is None):
      now = datetime.now().date()
      anno = now.year
      if now.month <= 9: #siamo in inverno -estate, data inizio = settembre anno precedente
        anno = anno - 1
      
      stats = Statistiche()
      stats.numeroCommissioni = Commissione.all().filter("numCommissari >",0).count()
      stats.numeroSchede = StatisticheIspezioni.all().filter("commissione",None).filter("centroCucina",None).filter("timeId",anno).get().numeroSchede
      stats.ncTotali = StatisticheNonconf.all().filter("commissione",None).filter("centroCucina",None).filter("timeId",anno).get().numeroNonconf
      stats.diete = Dieta.all().count()
      stats.note = Nota.all().count()
      stats.anno1 = anno
      stats.anno2 = anno + 1
      memcache.add("stats", stats)
      
    return stats
    
class CMSupportoHandler(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "supporto.html"
    self.getBase(template_values)
    
class CMCondizioniHandler(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "condizioni.html"
    self.getBase(template_values)

class CMRegistrazioneHandler(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "registrazione.html"
    self.getBase(template_values)
    
class CMMenuDataHandler(CMMenuHandler):
  
  def get(self): 
    if( self.request.get("cmd") == "getbydate" ):
      menu = Menu();
      data = datetime.strptime(self.request.get("data"),DATE_FORMAT).date()
      c = Commissione.get(self.request.get("commissione"))
      menu = self.getMenu(data, c)[0]
      
      self.response.out.write(menu.primo)
      self.response.out.write("|")
      self.response.out.write(menu.secondo)
      self.response.out.write("|")
      self.response.out.write(menu.contorno)
      self.response.out.write("\n")
        
class CMMapDataHandler(webapp.RequestHandler):
  
  def get(self): 
    limit = 100
    if self.request.get("limit"):
      limit = int(self.request.get("limit"))    
    offset = 0
    if self.request.get("offset"):
      offset = int(self.request.get("offset"))    

    if self.request.get("cmd") == "all":
      markers = memcache.get("markers_all"+str(offset))
      if(markers == None):
          
        commissioni = Commissione.all().order("nome").fetch(limit, offset);
          
        markers = "<markers>\n"
        try:
          for c in commissioni :
            if c.geo:
              markers = markers + '<marker key="' + str(c.key()) + '" nome="' + c.nome + '" indirizzo="' + c.strada + ', ' + c.civico + ', ' + c.cap + " " + c.citta + '"'
              markers = markers + ' lat="' + str(c.geo.lat) + '" lon="' + str(c.geo.lon) + '" tipo="' + c.tipoScuola + '" numcm="' + str(c.numCommissari) + '" cc="' + c.getCentroCucina().key().name() + '" />\n'
        except db.Timeout:
          logging.error("Timeout")
          
        markers = markers + "</markers>"    
        memcache.add("markers_all"+str(offset), markers)
      
      #logging.info(markers)
      self.response.headers["Content-Type"] = "text/xml"
      self.response.out.write(markers)      
    else:
      markers = memcache.get("markers")
      if(markers == None):
          
        commissioni = Commissione.all().filter("numCommissari >", 0)
          
        markers = "<markers>\n"
        try:
          for c in commissioni :
            if c.geo :
              markers = markers + '<marker key="' + str(c.key()) + '" nome="' + c.nome + '" indirizzo="' + c.strada + ', ' + c.civico + ', ' + c.cap + " " + c.citta + '"'
              markers = markers + ' lat="' + str(c.geo.lat) + '" lon="' + str(c.geo.lon) + '" tipo="' + c.tipoScuola + '" numcm="' + str(c.numCommissari) + '" cc="' + c.centroCucina.key().name() + '" />\n'
        except db.Timeout:
          logging.error("Timeout")
          
        markers = markers + "</markers>"    
        memcache.add("markers", markers)
      
      #logging.info(markers)
      self.response.headers["Content-Type"] = "text/xml"
      self.response.out.write(markers)

class DocPage(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "docs.html"
    template_values["iframesrc"] = "http://docs.pappa-mi.it/allegati"
    self.getBase(template_values)

class BlogPage(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "docs.html"
    template_values["iframesrc"] = "http://blog.pappa-mi.it/"
    self.getBase(template_values)

class FbPage(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "fb.html"
    self.getBase(template_values)

class ChiSiamoPage(BasePage):
  
  def get(self):
    template_values = dict()
    template_values["content"] = "chi.html"
    self.getBase(template_values)
    
def main():
  debug = os.environ['HTTP_HOST'].startswith('localhost')   

  application = webapp.WSGIApplication([
  ('/', MainPage),
  #('/fb', FbPage),
  ('/docs', DocPage),
  #('/blog', BlogPage),
  ('/chi', ChiSiamoPage),
  ('/map', CMMapDataHandler),
  ('/menu', CMMenuDataHandler),
  ('/supporto', CMSupportoHandler),
  ('/condizioni', CMCondizioniHandler),
  ('/registrazione', CMRegistrazioneHandler)
  ], debug=debug)
  
  wsgiref.handlers.CGIHandler().run(application)

#def profile_main():
    ## This is the main function for profiling
    ## We've renamed our original main() above to real_main()
    #import cProfile, pstats
    #prof = cProfile.Profile()
    #prof = prof.runctx("real_main()", globals(), locals())
    #print "<pre>"
    #stats = pstats.Stats(prof)
    #stats.sort_stats("time")  # Or cumulative
    #stats.print_stats(100)  # 80 = how many to print
    ## The rest is optional.
    ##stats.print_callees()
    ##stats.print_callers()
    #print "</pre>"  

#import py.dblog
#py.dblog.patch_appengine()    
    
if __name__ == "__main__":
  main()
  