"""GENERIC HANDLER
  Template for handler tools.
  Unless stated otherwise, code here is adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/__init__.py
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
from __future__ import with_statement
from os import chmod

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
class Message:
    def __init__(self, status, *args):
        '''Process according to status.'''
        if status == 'r':
            self._read(args[0])
        elif status == 's':
            self._send(contact=args[0], headers=args[1],
                       body=args[2], attachments=args[3])
        else:
            raise Exception('Invalid status %s' % status)
    
    def _read(self, text_string):
        """Parse message according to mode.
        * parse message
        * insert to database
        * send response
        * update sending status
        
        Keyword argument:
        text_string -- message to be parsed
        """
        self.msg = self.parse_message(text_string)
        msg_resp = self.process_message()
        self.insert_database()
        for elem in msg_resp:
            # TO DO: fork for each message!
            self._send(elem['contact'], elem['headers'],
                       elem['body'], elem['attachments'])
            # update status in database
            # possibly give option for user to resend
    
    def _send(self, contact, headers, body, attachments):
        """Send message according to mode.
        * Reconstruct message
        * insert to database
        * send message
        * update sending status
        
        Keyword argument:
        text_string -- message to be parsed
        """
        msg = self.construct_message(contact, headers, body, attachments)
        self.update_send_status(self.send_message(msg))
    
    def parse_message(self):
        raise NotImplementedError()
    
    def process_message(self):
        raise NotImplementedError()
    
    def insert_database(self):
        '''Don't forget db.commit()!'''
        raise NotImplementedError()
    
    def construct_message(self):
        raise NotImplementedError()
    
    def write_file(self, myfile, msg):
        """Write contents of msg to file path given by myfile.
        Adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_utils/fileutil.py
        """
        with file(myfile, 'w') as f:
            f.write(msg)
            chmod(f.name,0666)
            return myfile
        return ''
    
    def send_message(self):
        raise NotImplementedError()
    
    def update_send_status(self):
        raise NotImplementedError()
