"""
EMAIL HANDLER
  Tools for email messages.

Adapted from
  code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/
  emailhandler.py

Rules to follow:
  http://www.python.org/dev/peps/pep-0008/
  http://www.python.org/dev/peps/pep-0257/
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports

# related third party imports

# local application/library specific imports
import handler_generic

# CODE STARTS HERE -----------------------------------------------------------
class Reader(handler_generic.Reader):
    def __init__(self, text_string):
        """Parse message as email.
        
        Keyword arguments:
        text_string -- message to be parsed
        
        """
        print text_string[:5]

class Sender:
    pass

