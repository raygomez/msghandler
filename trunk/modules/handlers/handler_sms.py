"""SMS HANDLER
  Tools for SMS messages.
  Adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/smshandler.py
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
import email
import datetime
import tempfile

# related third party imports

# local application/library specific imports
import handler_generic

# CODE STARTS HERE -----------------------------------------------------------
class Message(handler_generic.Message):
    def parse_message(self, text_string):
        msg = email.message_from_string(text_string)
        self.attachments = {}
        self.headers = self.get_headers(msg)
    
    def process_message(self):
        return []
    
    def insert_database(self):
        '''Don't forget db.commit()!'''
        return 0
    
    def construct_message(self, contact, headers, body, attachments):
        return "To: %s\n\n%s\n" % (contact, body)
    
    def send_message(self, msg):
        print msg
    
    def update_send_status(self):
        return
    
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
