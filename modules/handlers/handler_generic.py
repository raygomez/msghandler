"""GENERIC HANDLER
  Template for handler tools.
  Adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/__init__.py
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports

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
            self._send(elem['contact'], elem['headers'],
                       elem['body'], elem['attachments'])
    
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
        self.send_message(msg)
    
    def parse_message(self):
        raise NotImplementedError()
    
    def process_message(self):
        raise NotImplementedError()
    
    def insert_database(self):
        '''Don't forget db.commit()!'''
        raise NotImplementedError()
    
    def construct_message(self):
        raise NotImplementedError()
    
    def send_message(self):
        raise NotImplementedError()
    
    def update_send_status(self):
        raise NotImplementedError()
