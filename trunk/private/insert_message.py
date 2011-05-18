"""MESSAGE PARSER
  Parses messages according to mode and inserts to database.

Run with
  python web2py.py -S msghandler -M -N -R applications/msghandler/private/insert_message.py -A <mode> <file_path>

Parameters
  <mode>: available values are email, sms
  <file_path>: complete path for the message to be read.
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
from __future__ import with_statement
from contextlib import closing
import traceback

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
args = os.sys.argv[1:]

try:
    '''Raise exceptions on error cases.'''
    if args[0] in ('h', 'help'):
        raise Exception(__doc__)
    if len(args) != 2:
        raise Exception(__doc__)
    
    with closing(open(args[1])) as f:
        text_string = f.read()
    
    handler = __import__('applications.%s.modules.handlers.handler_%s'
                         % (request.application, args[0]),
                         globals(), locals(), ['Message',], -1)

    x = handler.Message('r', text_string)
except Exception, e:
    '''Print exception and traceback information.'''
    print '\n', e
    exceptionType, exceptionValue, exceptionTraceback = os.sys.exc_info()
    print ''.join(traceback.format_exception(exceptionType,
                                             exceptionValue,
                                             exceptionTraceback))