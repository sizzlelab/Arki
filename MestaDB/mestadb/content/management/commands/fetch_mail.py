# -*- coding: utf-8 -*-
import imaplib
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand
from content.models import Mail

settings.DEBUG = False

import logging
log = logging.getLogger('fetch_mail')

def imap_connect(host):
    try:
        return imaplib.IMAP4_SSL(host = host)
    except:
        log.error("Failed to open IMAP4_SSL-connection to %s" % (host))
        return None
    #    raise

def imap_disconnect(M):
    M.close()
    M.logout()

def fetch_message(M, msgnum, delete_msg = True):
    log.info("Starting to fetch mail %s" % msgnum)
    typ, data = M.fetch(msgnum, '(RFC822)')
    log.info("Fetch done: %s. Saving message as a Mail object." % typ)
    mailfiledata = data[0][1]
    mail = Mail()
    mail.set_file(mailfiledata, M.host)
    log.info("Save done")
    if typ == 'OK':
        log.info("Status ok. Setting Deleted FLAGS: %s" % delete_msg)
        if delete_msg:
            M.store(msgnum, '+FLAGS', '\\Deleted')
    else:
        log.info("Status %s" % typ)
    return mail

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
    # Don't delete mail from INBOX after retrieving it
    option_list = option_list + (
        make_option('--nodelete',
                    action='store_true',
                    dest='nodelete',
                    default=False,
                    help=u'Do not delete mail from INBOX after retrieving it'),
        )
    args = ''
    help = 'Fetch Content mails from IMAP mailbox'

    def handle(self, *args, **options):
        limit = options.get('limit')
        verbosity = options.get('verbosity')
        nodelete = options.get('nodelete')
        delete = not nodelete
        imapconf = settings.MAILCONF
        login, passwd = imapconf['login'], imapconf['passwd']
        host = imapconf['host']
        M = imap_connect(imapconf['host'])
        if M is None:
            log.error("Failed to imap_connect(%s)" % imapconf['host'])
            return False
        try:
            typ, data = M.login(login, passwd)
        except Exception, err:
            log.error("Failed to login(%s) to host %s: %s" % (login, host, str(err)))
            return False
        try:
            M.select()
            typ, data = M.search(None, 'ALL')
        except Exception, err:
            log.error("Failed to select or search %s's mailbox on host %s: %s" % (login, host, str(err)))
            imap_disconnect(M)
        msg_ids = data[0].split()
        # Fetch 'limit' messages from INBOX
        cnt = 0
        try:
            for msgnum in msg_ids:
                fetch_message(M, msgnum, delete_msg = delete)
                cnt += 1
                if limit > 0 and cnt >= limit:
                    break
        except Exception, err:
            log.error("IMAP command failed: %s" % str(err))
            imap_disconnect(M)
        M.expunge()
        imap_disconnect(M)
