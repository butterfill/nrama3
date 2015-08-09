#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Methods for persisting nrama objects (create them using the nrama module).
  Depends on python-couchdb
"""


import couchdb

class db():
  def __init__(self, db_url, db_name, username=None, password=None):
    self.couch = couchdb.Server(db_url)
    if username is not None and password is not None:
      self.couch.resource.credentials = (username, password)
    self.db = self.couch[db_name]
    
  def save_or_update(self, doc):
    # *TODO check it doesn't already exist
    _id = doc['_id']
    if doc['_id'] in self.db:
      old_doc = self.db[_id]
      # new_doc will eventually be the updated doc: first copy old_doc
      new_doc = {}
      new_doc.update(old_doc)
      # copy doc because we want to delete some properties to avoid updating them
      to_update = {}
      to_update.update(doc)
      # if 'created' in to_update:
      #   del to_update['created']
      # if 'updated' in to_update:
      #   del to_update['updated']
      new_doc.update(to_update)
      self.db[_id] = new_doc
    else:
      self.db[_id] = doc


