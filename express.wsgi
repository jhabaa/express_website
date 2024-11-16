#!/usr/bin/python
import sys
import logging
import os

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/express/")
os.environ['FLASK_APP'] = 'express'
os.environ['FLASK_ENV'] = 'production'
from app import app as application
