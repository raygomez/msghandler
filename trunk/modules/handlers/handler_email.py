"""EMAIL HANDLER
  Tools for email messages.
  Unless stated otherwise, code here is adapted from code.google.com/p/ph-sms/source/browse/trunk/python/mh_handlers/emailhandler.py
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
import email

# related third party imports

# local application/library specific imports
import handler_generic

# CODE STARTS HERE -----------------------------------------------------------
class Message(handler_generic.Message):
    def parse_message(self, text_string):
        '''Parse message using RFC 2822.'''
        return email.message_from_string(text_string)
    
    def process_message(self):
        return []
    
    def insert_database(self):
        '''Don't forget db.commit()!'''
        return 0
    
    def construct_message(self):
        return
    
    def send_message(self):
        return 0
    
    def update_send_status(self):
        return 0
