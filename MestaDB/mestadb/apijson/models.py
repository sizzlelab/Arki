"""
:mod:`ocm.api.models` defines the models used in ocm's API.
"""

__id__ = "$Id$"

#from django.db import models
#from django.contrib import admin
#from django.contrib.auth.models import User
#
#class EventLogEntry(models.Model):
#    """
#    Simple event log object.
#    """
#    user = models.ForeignKey(User)
#    status = models.CharField(max_length=200)
#    command = models.CharField(max_length=200)
#    message = models.TextField()
#    added = models.DateTimeField(auto_now=True)
#    def __unicode__(self):
#        return "%s %s %s %s %s" % (self.user, self.status,
#                                   self.command, self.message, self.added)
