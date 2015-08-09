#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Functions to (a) extract skim notes from a pdf and (b) turn skim notes into objects.

Requires that skimnotes cli tool is on path (relies on shell commands to get notes from pdf file).

Use like skim_extract.get_notes("filename.pdf")

The result is a list of quote dictionaries; some quotes may contain a 'notes' field, which is a list of 
note dictionaries.  
"""


#for running skimnotes via shell
import subprocess
import shlex

# for tidying notes
import re


HIGHLIGHT = re.compile(u'^[*•] (Highlight|Evidenziazione), ')
NOTE = re.compile(u'^[*•] (Anchored Note|Nota ancorata), ')

def is_highlight(paragraph):
  return HIGHLIGHT.search(paragraph)
  
def is_note(paragraph):
  return NOTE.search(paragraph)

# testing only  
assert (is_highlight(u"• Evidenziazione, page whatever"))
assert (is_highlight(u"• Highlight, page whatever"))
assert (is_highlight(u"* Evidenziazione, page whatever"))
assert (is_highlight(u"* Highlight, page whatever"))
assert (not is_highlight(u"* Highzione, page whatever"))


PAGE_NUM = re.compile('^[p|P]age ')
def get_page_num(txt):
  return PAGE_NUM.sub('',txt)

#re to eliminate hyphens like "pyro- technic"
HYPHENS = re.compile('([a-zA-Z])- ([a-z])')

def clean_quote_text(txt):
  """1. remove hyphens like "pyro- technic"
  """
  txt = HYPHENS.sub(r'\1\2',txt)
  return txt


def _parse_quote(paragraph1,paragraph2):
  u"""a quote looks like this:
      \xe2\x80\xa2 Highlight, page 23       //paragraph1
      Clever things to say about whatever.  //paragraph2
  """
  page_text = HIGHLIGHT.sub('', paragraph1)  #remove '* Anchored Note, '
  page_num = get_page_num(page_text)
  content = clean_quote_text(paragraph2).decode('utf-8')
  page_number = page_num.decode('utf-8')
  quote_text = u"‘%s’ (p.~%s)" % ( content , page_number )
  quote = dict(content=quote_text, page_number=page_num, type='quote')
  return quote



def _parse_quote_with_notes(paragraphs):
  u""" a quote with notes looks like this
        • Anchored Note, page 6               # first paragraph
        coming out of the factory one day,    # second paragraph - quote text
        this is an example of joint           # third paragraph - note
        ...
        (The apology indicates there was)     # nth paragraph - note
  """
  #first paragraph is the page number
  para1 = paragraphs[0]
  page_text = NOTE.sub('', para1)  #remove '* Anchored Note, '
  page_num = get_page_num(page_text)
  quote_text = u''
  # second paragraph is the quote content, possibly edited by user
  raw_quote_text = paragraphs[1].decode('utf-8')
  add_quotes = True
  if u'‘' in raw_quote_text or u"'" in raw_quote_text or u'"' in raw_quote_text:
    # if user has added quotes to part, don't add quotes around the whole
    add_quotes = False
  if add_quotes:
    quote_text += u'‘'
  quote_text += clean_quote_text(raw_quote_text)
  if add_quotes:
    quote_text += u'’'
  quote_text += u' (p.~'+page_num+')' 
  quote = dict(page_number=page_num, content=quote_text, notes=[])
  # third paragraph onwards are notes
  for paragraph in paragraphs[2:]:
    note_text = paragraph.strip()
    if note_text is not "":
      note = dict(content=note_text, type='note')
      quote['notes'].append(note)
  return quote
    

def parse_notes(notes_txt):
  """Given some text in skim notes format, return a list of objects comprising
    sources, quotes and notes.
  """
  paragraphs = notes_txt.split('\n')
  res = []
  i = 0
  while i < len(paragraphs):
    paragraph = paragraphs[i].strip()
    # print  ('%d = %s'  ) % (i,paragraph)
    
    if paragraph == "":
      # blank line
      i += 1
      continue
    
    if is_highlight(paragraph):
      # new quote without notes attached
      i += 1
      next_para = paragraphs[i]
      quote = _parse_quote(paragraph,next_para)
      res.append(quote)
      i += 1
      continue
      
    if is_note(paragraph):
      # new quote with notes attached
      # print ": note\n"
      note_paragraphs = [paragraph]
      i+=1
      while i < len(paragraphs) and not is_highlight(paragraphs[i]) and not is_note(paragraphs[i]):
        paragraph = paragraphs[i]
        note_paragraphs.append(paragraph)
        i += 1
      quote_with_notes = _parse_quote_with_notes(note_paragraphs)
      res.append(quote_with_notes)
      continue
      
    #can't work out what the text is, just append it.
    # print ": misc"
    print "oops unknown thing: ",paragraph
    res.append(dict(content=paragraph,type='unknown'))
    i+=1
  return res
    
  
# use like cmd = shlex.split(CMD_TEMPATE % {'filename':"a.pdf"})
CMD_TEMPLATE = "skimnotes get -format text %(filename)s -"

def get_notes(filename):
  """extract skim notes from the specified filename
  return a text file
  """
  # build a shell command (shlex does escaping for us)
  cmd = shlex.split(str(CMD_TEMPLATE % {'filename':'"'+filename.encode('utf-8')+'"'}))
  # run the command and put the results in res
  res = subprocess.check_output(cmd)
  # res is the text of the notes; parse this and return the results
  return parse_notes(res)

