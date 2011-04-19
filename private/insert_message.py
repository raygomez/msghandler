"""
MESSAGE PARSER
  Parses messages according to mode and inserts to database.

Run with
  python web2py.py -S msghandler -M -N -R
  applications/msghandler/private/insert_message.py -A <mode> <file_path>

Adapted from
  code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/
  __init__.py

Rules to follow:
  http://www.python.org/dev/peps/pep-0008/
  http://www.python.org/dev/peps/pep-0257/
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
from __future__ import with_statement
from contextlib import closing

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
args = os.sys.argv[1:]

with closing(open(args[1])) as f:
    text_string = f.read()

handler = __import__('applications.%s.modules.handlers.handler_%s'
                        % (request.application, args[0]),
                     globals(), locals(), ['Reader',], -1)

x = handler.Reader(text_string)
