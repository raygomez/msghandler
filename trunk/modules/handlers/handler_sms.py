"""SMS HANDLER
  Tools for SMS messages.
  Unless stated otherwise, code here is adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/smshandler.py
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
import os.path
import email
import datetime
import tempfile
import time

# related third party imports

# local application/library specific imports
import handler_generic

# CODE STARTS HERE -----------------------------------------------------------
cfg = os.path.join(list(os.path.split(__file__))[0],'config')
cfg = __import__('.'.join(cfg.split('/')), globals(), locals(), ['',], -1)

class Message(handler_generic.Message):
    def parse_message(self, text_string):
        '''Parse message using RFC 2822.'''
        msg = email.message_from_string(text_string)
        self.attachments = {}
        self.headers = self.get_headers(msg)
    
    def process_message(self):
        return []
    
    def insert_database(self):
        '''Don't forget db.commit()!'''
        return 0
    
    def construct_message(self, contact, headers, body, attachments):
        '''Create message contents.'''
        return "To: %s\n\n%s\n" % (contact, body)
    
    def send_message(self, msg):
        """Write message to outgoing directory and return randomly generated
        filename.
        Adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_utils/fileutil.py
        """
        outfile = tempfile.mkstemp(prefix='send_', dir=cfg.sms_outgoing)
        filename = self.write_file(outfile[1], msg)
        return os.path.basename(filename)
    
    def update_send_status(self, filename):
        '''Return 1 on success and 0 on failure.'''
        while os.path.exists(os.path.join(cfg.sms_outgoing, filename)):
            time.sleep(20)
        if os.path.exists(os.path.join(cfg.sms_failed, filename)):
            return 0
        elif os.path.exists(os.path.join(cfg.sms_sent, filename)):
            return 1
        else:
            return -1
    
    def get_headers(self, msg):
        headers = dict(msg.items())
        # get contact
        self.contact = headers.pop('From')
        # parse dates
        headers['Date'] = headers['Sent'] = self.transform_date(headers.pop('Sent'))
        headers['Received'] = self.transform_date(headers.pop('Received'))
        # get body
        self.body = msg.get_payload()
        # 'Subject' is first line in text body
        headers['Subject'] = self.body.partition('\n')[0]
        return headers
    
    def transform_date(self, date_txt, date_fmt="%Y-%m-%d %H:%M:%S"):
        """Return formatted date as string.
        Assumes server time is synchronized to telco time.
        """
        val = datetime.datetime.strptime(date_txt, '%y-%m-%d %H:%M:%S')
        return val.strftime(date_fmt)
