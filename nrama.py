#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
  Methods for creating nrama objects.
"""

import time
import re
import hmac, base64, uuid

def make_uuid():
  return str(uuid.uuid4()).replace('-','')

def b64_hmac_md5(k,d):
  hmac_md5 = hmac.HMAC(k,d)
  b64= base64.b64encode(hmac_md5.digest())
  return b64[:-2]  #strip last two characters (these are "==", not sure why)


def convert_to_upper(field, d):
  upper_field = field.upper()
  if field in d:
    d[upper_field] = d[field]
    del d[field]

class sources():
  """functions for processing nrama sources"""
  @staticmethod
  def calculate_id(source):
    return 'source_'+b64_hmac_md5(source['user_id'].encode('utf-8'), source['page_id'].encode('utf-8'))
  
  @staticmethod
  def create(page_id, user_id, bibtex, created=None):
    if created is None:
      # utc epoch in milliseconds 
      created = int(time.time() * 1000)
    if 'title' in bibtex:
      # get rid of the {} from bibtex
      bibtex['title'] = bibtex['title'].replace('{','').replace('}','')
    new_source = {}
    new_source.update(bibtex)
    new_source.update( {
      'type' : 'source',
      'nrama_origin' : 'skim_notes',
      'page_id' : page_id,
      'title' : bibtex['title'],
      'page_title' : bibtex['title'],
      'user_id' : user_id,
      'bibtex' : bibtex,
      'created' : created,
      'updated' : created
    })
    convert_to_upper('author', new_source)
    convert_to_upper('doi', new_source)
    convert_to_upper('journal', new_source)
    convert_to_upper('booktitle', new_source)
    convert_to_upper('editor', new_source)
    convert_to_upper('publisher', new_source)
    convert_to_upper('address', new_source)
    convert_to_upper('issue', new_source)
    convert_to_upper('pages', new_source)
    convert_to_upper('volume', new_source)
    convert_to_upper('number', new_source)
    convert_to_upper('year', new_source)
    if 'title' in new_source:
      # some records have both cases of title
      new_source['TITLE'] = new_source['title']
      
    new_source['_id'] = sources.calculate_id(new_source)
    if 'url' not in new_source:
      if 'link' in bibtex:
        new_source['url'] = bibtex['link']
      else:
        if 'DOI' in bibtex:
          new_source['url'] = 'http://dx.doi.org/%s' % bibtex['DOI']
        else:
          new_source['url'] = 'http://filename.note-o-rama.com/%s' % new_source['_id']
    return new_source
  
class quotes():
  """functions for processing nrama quotes"""
  @staticmethod
  def calculate_hash(quote):
    return b64_hmac_md5(quote['page_id'].encode('utf-8'), quote['content'].encode('utf-8'))

  @staticmethod
  def create(source, content, page_number=None, created=None, **kw):
    if created is None:
      # utc epoch in milliseconds 
      created = int(time.time() * 1000)
    new_quote = {
      'type' : 'quote',
      'nrama_origin' : 'skim_notes',
      'content' : content.strip(),
      'page_id' : source['page_id'],  
      'page_title' : source['page_title'],
      'page_order' : page_number,
      'created' : created,
      'updated' : created,
      'user_id' : source['user_id'],
      'source_id' : source['_id']
    }
    hash = quotes.calculate_hash(new_quote)
    new_quote['hash'] = hash
    new_quote['_id'] = 'q_'+hash
    if 'url' in source:
      new_quote['url'] = source['url']
    new_quote.update(kw)
    return new_quote


class notes():
  
  @staticmethod
  def calculate_id(note):
    """
    Notes id is determined by user, quote and content.
    This ensures that you will never add multiple notes with the same content to the same quote for the same 
    user.
    """
    return 'n_'+b64_hmac_md5(note['user_id'].encode('utf-8'), note['quote_id'].encode('utf-8') + note['content'].encode('utf-8'))
  
  _hashtag_regex = re.compile('(^|[^0-9A-Z&\/\?]+)(#|＃)([0-9A-Z_]*[A-Z_\-]+[a-z0-9_]*)',re.IGNORECASE)
  @staticmethod
  def get_tags(text):
    tags = []
    tag_tupes = notes._hashtag_regex.findall(text)
    for tag_tuple in tag_tupes:
      tags.append(tag_tuple[2])
    # print "tags = ",tags
    return tags
  
  @staticmethod  
  def create(quote, content, created=None):
    if created is None:
      # utc epoch in milliseconds 
      created = int(time.time() * 1000)
    new_note = {
      'type' : 'note',
      'nrama_origin' : 'skim_notes',
      'content' : content,
      'quote_id' : quote['_id'],
      'quote_hash' : quote['hash'],       #can attach to the same quote from other users
      'tags' : notes.get_tags(content),   #cache the #tags to save us parsing text in creating a view
      'page_id' : quote['page_id'],  
      'created' : created,
      'updated' : created,
      'user_id' : quote['user_id'],
      'source_id' : quote['source_id']
    }
    new_note['_id'] = notes.calculate_id(new_note)
    return new_note
