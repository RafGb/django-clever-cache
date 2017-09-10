#!/usr/bin/env python
import os

import django
from django.core.management import call_command

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

django.setup()

call_command('test')
