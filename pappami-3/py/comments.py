#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from py.base import Const, BasePage, commissario_required, reguser_required, config, handle_404, handle_500

import os, cgi, logging, urllib, json
from datetime import date, datetime, time, timedelta
import wsgiref.handlers

from google.appengine.ext.ndb import model
import webapp2 as webapp
from google.appengine.api import memcache
from google.appengine.api import mail

from py.gviz_api import *
from py.model import *
#from py.site import *
from py.blob import *
from py.form import IspezioneForm, NonconformitaForm, DietaForm, NotaForm
from py.stats import CMStatsHandler
#from py.gcalendar import *
from py.modelMsg import *

TIME_FORMAT = "%H:%M"
DATE_FORMAT = "%Y-%m-%d"

"""
comment handler
handle both messages (comments not attached to other objects) and comments (comments attached to a "root" message object
"""
class CMCommentHandler(BasePage):

  """ 
  init a comment structure, attaching an empty root message to an existing object
  """
  @classmethod
  def init(cls, msg_rif, msg_grp, tipo, tags, user):
    messaggio = Messaggio.get_by_parent(msg_rif)
    if not messaggio:  
      messaggio = Messaggio()
      messaggio.par = msg_rif
      messaggio.root = msg_rif
      messaggio.grp = msg_grp
      messaggio.livello = 0
      messaggio.tipo = tipo
      messaggio.commenti = 0
      messaggio.c_ua = user.key
      messaggio.put()
      if tags:
        CMTagHandler.saveTags(messaggio, tags)
        
      messaggio.invalidate_cache();
    return messaggio

  """
  init a comment structure, attaching a root message to an existing object
  and return the delta activity stream html
  """
  @classmethod
  def initActivity(cls, msg_rif, msg_grp, tipo, last, tags, user):

    new_msg = CMCommentHandler.init(msg_rif, msg_grp, tipo, tags, user)
    
    return cls.loadActivity(last, new_msg.par)

  """
  """
  @classmethod
  def loadActivity(cls, last, item_key):

    buff = ""

    template_values = {
      'main': 'activity.html',
      'ease': True
    }

    if not last:
      last = Messaggio.get_by_parent(item_key)
    activities = Messaggio.get_all_from_item(last)
  
    template_values['activities'] = activities       

    return template_values
  
  """
  return the root object of a given message (comment)
  """
  @classmethod
  def getRoot(cls, msg_rif):
    return Messaggio.get_root(msg_rif)
  
  """
  http post handler
  handle both new message and new comment (livello is the discriminant)
  return the delta activity stream in html
  """
  @reguser_required
  def post(self):
    par_key = None
    rif = self.request.get("par")
    if rif:
      par_key = model.Key("Messaggio", int(rif))

    messaggio = Messaggio()
    messaggio.par = par_key
    messaggio.tipo = int(self.request.get("tipo"))
    messaggio.livello = int(self.request.get("livello"))
    messaggio.titolo = self.request.get("titolo")
    messaggio.testo = self.request.get("testo")
    messaggio.commenti = 0
    messaggio.c_ua = self.request.user.key    
    messaggio.put()

    logging.info("testo: " + self.request.get("testo"))
    logging.info("last: " + self.request.get("last"))
    
    messaggio.allegati = list()
    for i in range(1,10):
      if self.request.get('allegato_file_' + str(i)):
        if len(self.request.get('allegato_file' + str(i))) < 10000000 :
          allegato = Allegato()
          allegato.descrizione = self.request.get('allegato_desc_' + str(i))
          allegato.nome = self.request.POST['allegato_file_' + str(i)].filename
          blob = Blob()
          blob.create(allegato.nome)
          allegato.blob_key = blob.write(self.request.get('allegato_file_' + str(i)))
          allegato.obj = messaggio.key
          allegato.put()
          messaggio.allegati.append(allegato)
        else:
          logging.info("attachment is too big.")
    
    if messaggio.livello > 0 and par_key:
      par = par_key.get()
      commenti = par.commenti
      if commenti is None:
        commenti = 0
      par.commenti = commenti + 1
      par.put()
   
    CMTagHandler.saveTags(messaggio, self.request.get_all("tags"))
  
    template_values = {
      'activity': messaggio,
      'ease': True
    }
    messaggio.invalidate_cache();
    last_key = None
          
    if messaggio.livello == 0: #posting root message      
      last_key = messaggio.key
      if self.request.get("last") != "":
        last_key = model.Key("Messaggio", int(self.request.get("last")))
      template_values = self.loadActivity(last_key, None)
    else:
      if self.request.get("last") != "":
        last_key = model.Key("Messaggio", int(self.request.get("last")))
      activities = Messaggio.get_all_from_item_parent(last_key, messaggio)
  
      template_values['main'] = 'comments/comment.html'
      comment_root = model.Key("Messaggio",int(self.request.get("root"))).get()
  
      template_values['activities'] = activities
      template_values['comments'] = activities
      template_values['comment_root'] = comment_root

    return self.getBase(template_values)
    
  """
  load comments html put under a message
  """
  def get(self):
    root = self.request.get("par")
    commento_root = model.Key("Messaggio", int(root)).get()
    
    comments = list()
    if commento_root:      
      commenti = Messaggio.get_by_parent(commento_root.key)
      for msg in commenti:
        comments.append(msg)
      
    comment_last = None
    if len(comments):
      comment_last = comments[len(comments)-1]
      
    logging.info("comment_last: " + str(comment_last))
    template_values = {
      'main': 'comments/comment.html',
      'comment_root': commento_root,
      'comments': comments,
      'comment_last': comment_last,
      'last': comment_last,
      'ease': False
    }
    self.getBase(template_values)

class ActivityLoadHandler(BasePage):
  def get(self):

    template_values = {
      'main': 'activity.html',
      'ease': self.request.get("ease")
    }

    buff = ""
    
    offset = 0
    if self.request.get("offset") != "":
      offset = int(self.request.get("offset"))

    limit = None
    if self.request.get("limit") != "":     
      template_values['limit'] = int(self.request.get("limit"))
    template_values['activities'] = self.get_activities(offset)

    self.getBase(template_values)
    
  
class CMVoteHandler(BasePage):
  @reguser_required
  def get(self):
    messaggio = model.Key("Messaggio", int(self.request.get('msg'))).get()

    messaggio.vote(int(self.request.get('voto')), self.request.user)
    self.response.out.write(len(messaggio.votes))

class CMVotersHandler(BasePage):  
  def get(self):
    messaggio = model.Key("Messaggio", int(self.request.get('msg'))).get()    
    template_values = {
      'main': 'comments/voters.html',
      'votes': messaggio.votes
    }
    self.getBase(template_values)    

class CMTagHandler(BasePage):
  def get(self):
    alltags = list()
    assignedtags = list()
    msg = None
    if self.request.get('msg'):
      msg = model.Key("Messaggio", int(self.request.get('msg')))
    tagobjs = TagObj.get_by_obj_key(msg)
    for tagobj in tagobjs:
      assignedtags.append(tagobj.tag.get().nome)
    for tag in Tag.get_all():
      alltags.append(tag.nome)

    buff = json.JSONEncoder().encode({'assignedTags': assignedtags, 'availableTags':alltags})      
    self.response.out.write(buff)
    
  @reguser_required
  def post(self):
    tagnames = self.request.get_all("tags")
      
    CMTagHandler.saveTags(messaggio.Key("Messaggio", int(self.request.get('msg'))),tagnames)

    buff = json.JSONEncoder().encode({'status': 'ok'})      
    self.response.out.write(buff)
    
  @classmethod
  def saveTags(cls,obj,tagnames):
    logging.info("tags")
    tagobjs = TagObj.get_by_obj_key(obj.key)
    tagold = dict()
    for tagobj in tagobjs:
      tagold[tagobj.tag.nome] = tagobj
    for tagname in tagnames:
      logging.info("tagname: " + tagname)
      if (tagname in tagold) is False:
        logging.info("adding: " + tagname)
        tag = Tag.get_by_name(tagname)
        if not tag:
          tag = Tag(nome=tagname, numRef=0)
          tag.c_ua = obj.c_ua
          tag.put()
        tagobj = TagObj(tag=tag.key,obj=obj.key)
        tagobj.put()
        tag = tagobj.tag.get()
        tag.numRef += 1
        tag.put()
    for name in tagold:
      logging.info(name)
      
      if (name in tagnames) is False:
        logging.info("removing:" + name)
        tagobj = tagold[name]
        tag = tagobj.tag.get()
        tag.numRef -= 1
        tag.put()
        tagobj.key.delete()
        
  def getTags(self):
    tags = Tag.get_all()
    return tags
    
    
app = webapp.WSGIApplication([
    ('/comments/load', ActivityLoadHandler),
    ('/comments/message', CMCommentHandler),
    ('/comments/comment', CMCommentHandler),
    ('/comments/vote', CMVoteHandler),
    ('/comments/voters', CMVotersHandler),
    ('/comments/gettags', CMTagHandler), 
    ('/comments/updatetags', CMTagHandler)    
  ], debug=os.environ['HTTP_HOST'].startswith('localhost'), config=config)

app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500

def main():
  app.run();

if __name__ == "__main__":
  main()