# -*- coding: utf-8 -*-
import email
import sys
import os
import re
import datetime
from dateutil import tz
import time
from optparse import make_option
from django.contrib.auth.models import User

from django.db import transaction
from django.db.models import Count #, Avg, Max, Min
from django.core.management.base import BaseCommand #, CommandError
from django.conf import settings
settings.DEBUG = False

import logging
log = logging.getLogger('fetch_mail')

from content.models import Content, Mail

# Helpers
def get_subject(msg):
    """
    Parse and decode msg's Subject.
    TODO: return meaningful value if Subject was not found, raise error when there is error
    TODO: link to the RFC.
    """
    try:
         subject_all = email.Header.decode_header(msg.get_all('Subject')[0])
    except:
        # TOD: Should we return false here?
        subject_all = []
    # Subject_all is a tuple, 1st item is Subject and 2nd item is possible encoding
    # [("Jimmy & Player's Bar", None)]
    # [('Fudiskent\xe4t vihert\xe4v\xe4t', 'iso-8859-1')]
    subject_list = []
    for word in subject_all:
        if word[1] is not None: # Try first to use encoding guessed by email-module
            #print "ANNETTU, " , word
            try:
                subject_list.append(unicode(word[0], word[1]))
            except: # UnicodeDecodeError: 'iso2022_jp' codec can't decode byte 0x81 in position 0: illegal multibyte sequence
                subject_list.append(unicode(word[0], errors='replace'))
        else:
            try: # Try first latin-1, it's the best guess in western Europe
                #print "UTFIAAA, " , word
                subject_list.append(unicode(word[0], 'utf-8', errors='replace'))
            except UnicodeError: # Final fallback, use utf-8 and replace errors
                #print "LATINAA, " , word
                subject_list.append(unicode(word[0], 'latin-1'))
    try:
        subject = u' '.join(subject_list)
        # Remove extra whitespaces (TODO: use some wiser method here
        subject = subject.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ').replace('  ', ' ')
    except:
        return False
    return subject

def get_recipient(msg):
    """
    Loop 'to_headers' until an email address(s) is found.
    Some mail servers use Envelope-to header.
    """
    to_headers = ['envelope-to', 'to', 'cc', ]
    tos = []
    while len(tos) == 0 and len(to_headers) > 0:
        tos = msg.get_all(to_headers.pop(0), [])
    return tos

def handle_part(part):
    filename = part.get_filename()
    filedata = part.get_payload(decode=1)
    return filename, filedata

def savefiles(msg):
    """
    Extract parts from  msg (which is an email.message_from_string(str) instance)
    and send them to the plok-database.
    NOTES:
    - uses only the first found email address to assume recipient
    """
    part_counter = 1
    subject = get_subject(msg)
    tos = get_recipient(msg)
    msg_id = msg.get('message-id', '')
    froms = msg.get_all('from', [])
    p = re.compile('([\w\.\-]+)@')
    try: # May raise in some cases IndexError: list index out of range
        matches = p.findall(froms[0])
        sender_nick = matches[0].split(".")[0].title() # Use all before first '.'
    except:
        print "ERROR: No From header %s" % (msg_id)
        return False
    print subject, tos, froms, msg_id
    if len(tos) == 0:
        print "ERROR: No Tos found %s" % (msg_id)
        return False
    p = re.compile('([\w]+)\.([\w]+)@') # e.g. user.authtoken@plok.in
    matches = p.findall(tos[0])
    if len(matches) > 0:
        user = matches[0][0].title()
        key = matches[0][1].lower()
    else:
        print "ERROR: No user.authkey found from %s %s" % (tos[0], msg_id)
        return False
    # TODO: replace this with AuthTicket stuff
    from django.contrib.auth import authenticate
    user = authenticate(authtoken='qwerty123')
    print user
    parts_not_to_save = ["multipart/mixed",
                         "multipart/alternative",
                         "multipart/related",
                         "text/plain",
                         ]
    saved_parts = 0
    for part in msg.walk():
        part_content_type = part.get_content_type()
        if part_content_type in parts_not_to_save:
            # print "NOT SAVING", part_content_type
            continue
        print part_content_type
        filename, filedata = handle_part(part)
        if filename is None:
            print "No filename"
            continue
        c = Content(
            user = user,
            #privacy = legal_key_map[key],
            caption = subject,
            author = sender_nick,
        )
        c.set_file(filename, filedata)
        c.get_type_instance()
        c.save()
        print c
        saved_parts += 1
    return saved_parts


def process_mails(limit=0, move=True):
    mails = Mail.objects.filter(status='UNPROCESSED').order_by('created')
    if limit > 0:
        mails = mails[:limit]
    for mail in mails:
        path = mail.file.path
        with open(path, 'rt') as f:
            maildata = f.read()
        msg = email.message_from_string(maildata)
        if savefiles(msg):
            mail.status = 'PROCESSED'
        else:
            mail.status = 'FAILED'
        mail.save()

class Command(BaseCommand):
    # Limit max number of mails to process
    option_list = BaseCommand.option_list + (
        make_option('--limit',
                    action='store',
                    dest='limit',
                    type='int',
                    default=0,
                    help='Limit the number of mails to handle'),
        )
    # Don't move mail from 'new' to 'processed'/'failed' after processing it
    option_list = option_list + (
        make_option('--nomove',
                    action='store_true',
                    dest='nomove',
                    default=False,
                    help=u'Do not move mail from "new" after retrieving it'),
        )
    args = ''
    help = 'Process new retrieved mails'

    def handle(self, *args, **options):
        limit = options.get('limit')
        verbosity = options.get('verbosity')
        nomove = options.get('nomove')
        move = not nomove
        process_mails(limit=limit, move=move)
