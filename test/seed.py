'''
Created on Jun 14, 2011

@author: thatcherclay
'''

import sys, os
sys.path.append(os.getcwd()+"/../output-tests/")
sys.path.append(os.getcwd()+"/../output-tests/web/")

os.environ['DJANGO_SETTINGS_MODULE'] = 'web.settings'

from mailreceipts.models import *
from django.contrib.auth.models import User

def createUser(user, password):
    if not User.objects.filter(username=user).exists():
        return User.objects.create_user(user, user, password)
    else:
        return User.objects.get(username=user)


    
    