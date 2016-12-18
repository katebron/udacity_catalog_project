#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/cat_app")

from cat_app import app as application
application.secret_key = 'Add your secret key'
