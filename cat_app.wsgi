#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/cat_app")

from cat_app import app as application
application.secret_key = '3\x0cU\xb0\xbe\xea\x7f\xd4c=\x85-\tGB\x1eV\xc7hPi\xd5c\xcf'
