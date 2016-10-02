#!/usr/bin/env python
# -*- coding: utf-8 -*-

# take a .bib bibtex file, look up the pdfs, extract the skim notes and put the results into a database
# the parameters (filename, db name etc) are hardcoded below

# create the .bib file by using zotero's extract function

# requires pip install bibtexparser
# requires pip install couchdb #python-couchdb

# FILENAME Is the name of bibtex file to get references and files from.
# This should be created by exporting from Zotero, or should have the 
#  pdf file name(s) is a colon-delimited field called 'file'.
FILENAME = './lib3.bib'
#_DB_URL = 'http://localhost:5984/'
_DB_URL = 'http://notes.butterfill.com/'
_DB_NAME = 'nrama'
USER_ID = 'steve'
PASSWORD = 'r4maqu3en'

import os

import skim_extract
import nrama, nrama_persist

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import *

def get_bibtex_db(filename):
  """@param filename is the name of a bibtex file
  Reads the file and converts it to a list of dictionary objects.
  """
  # ensures that authors are an ordered list (not just a string)
  def customizations(record):
      """Use some functions delivered by the library

      :param record: a record
      :returns: -- customized record
      """
      record = type(record)
      record = author(record)
      record = editor(record)
      return record

  bibtex_file = open(filename)
  parser = BibTexParser()
  parser.customization = customizations
  bib_db = bibtexparser.load(bibtex_file, parser=parser)
  return bib_db


def filter_pdf_filenames(filenames):
  """given a list of filenames, return those which point to pdf files
     and start with '/'
  """
  return [filename for filename in filenames if filename.startswith('/') and filename.endswith('.pdf')]

def clean_filenames(filenames):
  """
  because filenames come from bibtex parser, some escaping has occurred.
  I'm not sure exactly what; '&' is left alone but ';' gets escaped
  """
  return [f.replace('\;',';') for f in filenames]

# testing only
def print_dict(d):
  for k,v in d.items():
    print k, "=", v



def get_notes(bib_entry):
  """@param bib_entry is a bibtextparser entry
     Take the files specified in 'file', and for each pdf extract the notes.
     Return a dictionary with filenames and keys and note text as values.
  """
  # print bib_entry.keys()
  if 'file' not in bib_entry:
    return {}
  filenames = bib_entry['file'].split(':')
  filenames = filter_pdf_filenames(filenames)
  filenames = clean_filenames(filenames)
  res = {}
  for filename in filenames:
    print 'filename = ', filename
    notes = skim_extract.get_notes(filename)
    if notes is not None and notes != "":
      res[filename]=notes
  return res
    
bib_db = get_bibtex_db(FILENAME)



db = nrama_persist.db(_DB_URL, _DB_NAME, USER_ID,PASSWORD)


def process_entry(entry):
  """
  process a bibtex entry
  each entry may contain multiple filenames, so get notes from each file named.
  """
  notes_by_filenames  = get_notes(entry) #keys are filenames, values are the notes and quotes
  for filename in notes_by_filenames.keys():
    # -- first check there are notes or quotes to save
    notes_and_quotes = notes_by_filenames[filename]
    if notes_and_quotes is None or len(notes_and_quotes) is 0:
      # no notes and quotes
      continue
    # get time file changed (on *nix) and used this as created date
    created = int(os.path.getctime(filename)*1000)
    # -- second create and persist or update the source
    source = nrama.sources.create(page_id=filename, user_id=USER_ID, bibtex=entry, created=created)
    print 'filename = ', filename, "nof quotes = ",len(notes_and_quotes)
    db.save_or_update(source)
    # -- third, extract the notes and quotes and persist or update these
    for q in notes_and_quotes:
      if 'type' not in q or q['type'] is not 'quote':
        # this is not a quote
        continue
      quote = nrama.quotes.create(source=source, content=q['content'], page_number=q['page_number'], created=created)
      # print "\n---quote---"
      # print_dict(quote)
      db.save_or_update(quote)
      notes = []
      if 'notes' in q:
        notes = q['notes']
      for n in notes:
        note = nrama.notes.create(quote=quote, content=n['content'], created=created)
        db.save_or_update(note)
      


for entry in bib_db.entries:
  process_entry(entry)

# --- testing after here

# def print_dict(d):
#   for k,v in d.items():
#     print k, "=", v
#
# first_entry = bib_db.entries[0]
# process_entry(first_entry)
#
