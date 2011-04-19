# GENERIC HANDLER
#   Matches messages with the right application, regardless of mode
#   (SMS, email, etc).
#
# code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/
#   __init__.py
#

# Rules:
#   imports should follow PEP 8 (http://www.python.org/dev/peps/pep-0008/)
#   docstrings should follow PEP 257 (http://www.python.org/dev/peps/pep-0257/)

# IMPORTS START HERE ----------------------------------------------------------
# standard library imports

# related third party imports

# local application/library specific imports

# CODE STARTS HERE ------------------------------------------------------------
class Reader:
    def __init__(self, text_string):
        """Parse message according to mode.
        
        Keyword argument:
        text_string -- message to be parsed
        
        """
        raise NotImplementedError()

class Sender:
    def __init__(self):
        raise NotImplementedError()

