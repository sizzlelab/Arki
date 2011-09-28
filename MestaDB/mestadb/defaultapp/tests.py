"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.utils import unittest
from django.test import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

class FPTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.username = 'test'
        self.password = 'test'
        self.user = User.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()

    def test_user_login(self):
        """
        Tests login, requesting frontpage and logout
        """
        self.assertEqual(self.client.login(username=self.username, password=self.password), True)
        self.assertEqual(self.client.get(reverse('defaultapp_index')).status_code, 200)
        self.assertEqual(self.client.get(reverse('defaultapp_logout')).status_code, 302)
