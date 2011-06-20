# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:                                                          # if running on Google App Engine
    db = DAL('gae')                                                                                                                                                                                                 # connect to Google BigTable
                                                                                                                                                                                                                                                                                                                                                                            # optional DAL('gae://namespace')
    session.connect(request, response, db = db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
else:                                                                                                                                                                                                                                                                                                                               # else use a normal relational database
    db = DAL('sqlite://storage.sqlite')             # if not, use SQLite or other DB
## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import *
mail = Mail()                                                                                                                                             

class MyAuth(Auth):
     def __init__(self, environment, db = None):
         Auth.__init__(self,environment,db)
                                                                                                                   # mailer
auth = MyAuth(globals(),db)                                                                                                                                                    # authentication/authorization

db.define_table(
    auth.settings.table_user_name,
    Field('first_name', length=128, default=''),
    Field('last_name', length=128, default=''),
    Field('email', length=128, default='', unique=True,
        writable=False, readable=False, ),
    Field('username', length=128, default=""),
    Field('password', 'password', length=512,
          readable=False, label='Password'),
    Field('profession', length=128, default=''),
    Field('prc', 'integer', default=''),    
    Field('registration_key', length=512,
          writable=False, readable=False, default=''),
    Field('reset_password_key', length=512,
          writable=False, readable=False, default=''),
    Field('registration_id', length=512,
          writable=False, readable=False, default=''))

custom_auth_table = db[auth.settings.table_user_name] # get the custom_auth_table
custom_auth_table.first_name.requires = \
  IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.last_name.requires = \
  IS_NOT_EMPTY(error_message=auth.messages.is_empty)
custom_auth_table.password.requires = [CRYPT()]
custom_auth_table.username.requires = IS_NOT_IN_DB(db, custom_auth_table.username)
#custom_auth_table.email.requires = [
#  IS_EMAIL(error_message=auth.messages.invalid_email),
#  IS_NOT_IN_DB(db, custom_auth_table.email)]

auth.settings.table_user = custom_auth_table # tell auth to use custom_auth_table

crud = Crud(globals(),db)                                                                                                                                                    # for CRUD helpers using auth
service = Service(globals())                                                                                                                         # for json, xml, jsonrpc, xmlrpc, amfrpc
plugins = PluginManager()

mail.settings.server = 'logging' or 'smtp.gmail.com:587'  # your SMTP server
mail.settings.sender = 'telehealth.up@gmail.com'                               # your email
mail.settings.login = '#'    # your credentials or None

auth.settings.hmac_key = 'sha512:7170c6c3-cd99-4212-beb9-41135103ac81'   # before define_tables()
auth.define_tables()                                                                                                                                                                                                 # creates all needed tables
auth.settings.mailer = mail                                                                                                                                  # for user email verification
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.messages.verify_email = 'Click on the link http://'+request.env.http_host+URL('default','user',args=['verify_email'])+'/%(key)s to verify your email'
auth.settings.reset_password_requires_verification = True
auth.settings.actions_disabled = ['register','profile']
auth.messages.reset_password = 'Click on the link http://'+request.env.http_host+URL('default','user',args=['reset_password'])+'/%(key)s to reset your password'

#########################################################################
## If you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, uncomment and customize following
# from gluon.contrib.login_methods.rpx_account import RPXAccount
# auth.settings.actions_disabled=['register','change_password','request_reset_password']
# auth.settings.login_form = RPXAccount(request, api_key='...',domain='...',
#    url = "http://localhost:8000/%s/default/user/login" % request.application)
## other login methods are in gluon/contrib/login_methods
#########################################################################

crud.settings.auth = None                                                                                                                                                    # =auth to enforce authorization on crud

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##             'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

from datetime import datetime
import os

db.define_table('contact',
    Field('user_id', db.auth_user),
    Field('contact_type', notnull=True, requires=IS_IN_SET(('mobile', 'landline', 'email'))),
    Field('contact_info', notnull=True),
    format='%(contact_info)s')
db.contact.user_id.requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s')

db.define_table('msg',
    Field('subject', notnull=True),
    Field('content', 'text', notnull=True),
    Field('created_by', db.contact, notnull=True),
    Field('parent_msg', 'reference msg', notnull=True, default=0),    
    Field('create_time', 'datetime', notnull=True, default=datetime.now()),
    Field('is_hidden', 'boolean', default=False),
    Field('is_closed', 'boolean', default=False),
    format='%(subject)s')
db.msg.created_by.requires=IS_IN_DB(db, 'contact.id', '%(contact_info)s')
db.msg.created_by.writable = db.msg.created_by.readable = False
db.msg.create_time.writable = db.msg.create_time.readable = False
db.msg.parent_msg.writable = db.msg.parent_msg.readable = False
db.msg.is_hidden.writable = db.msg.is_hidden.readable = False
db.msg.is_closed.writable = db.msg.is_closed.readable = False

db.define_table('msg_attachment',
    Field('msg_id', db.msg, notnull=True),
    Field('attach_time', 'datetime', notnull=True, default=datetime.now()),
    Field('attachment_type', notnull=True, default='image'),
    Field('attach_by', db.contact, notnull=True),
    Field('filename'),
    Field('attachment', 'upload', notnull=True),
    format='%(filename)s')
db.msg_attachment.msg_id.requires = IS_IN_DB(db, 'msg.id')
db.msg_attachment.msg_id.writable = db.msg_attachment.msg_id.readable = False
db.msg_attachment.attach_time.writable = db.msg_attachment.attach_time.readable = False
db.msg_attachment.attach_by.writable = db.msg_attachment.attach_by.readable = False
db.msg_attachment.attachment_type.writable = db.msg_attachment.attachment_type.readable = False
db.msg_attachment.filename.writable = db.msg_attachment.filename.readable = False

db.define_table('msg_recipients',
    Field('msg_id', db.msg),
    Field('contact_id', db.contact),
    Field('process_time', 'datetime'),
    format='%(msg_id.subject)s %(contact_id.contact_info)s')
db.msg_recipients.msg_id.requires=IS_IN_DB(db, 'msg.id', '%(subject)s')
db.msg_recipients.contact_id.requires=IS_IN_DB(db, 'contact.id', '%(contact_info)s')

db.define_table('tag',
    Field('name', notnull=True),
    Field('description', 'text', notnull=True),
    format='%(name)s')
db.tag.name.requires=IS_NOT_IN_DB(db, 'tag.name')

db.define_table('msg_group',
    Field('msg_id',  db.msg, notnull=True),
    Field('group_id', db.auth_group, notnull=True), 
    Field('assigned_to', db.auth_user),
    Field('assigned_by', db.auth_user),
    Field('assign_time', 'datetime', notnull=True, default=datetime.now()),
    format='%(msg_id.subject)s %(group_id.role)s')
db.msg_group.msg_id.requires=IS_IN_DB(db, 'msg.id', '%(subject)s')
db.msg_group.group_id.requires=IS_IN_DB(db, 'auth_group.id', '%(role)s')    
db.msg_group.assigned_to.requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')    
db.msg_group.assigned_by.requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')    
db.msg_group.assigned_by.writable = db.msg_group.assigned_by.readable = False

db.define_table('msg_tag',
    Field('msg_id', db.msg),
    Field('tag_id', db.tag),
    Field('tag_time', 'datetime', notnull=True, default=datetime.now()),
    format='%(tag_id.name)s %(msg_id.subject)s')
db.msg_tag.msg_id.requires=IS_IN_DB(db, 'msg.id', '%(subject)s')
db.msg_tag.tag_id.requires=IS_IN_DB(db, 'tag.id', '%(name)s')

db.define_table('event',
    Field('timestamp','datetime', notnull=True, default=datetime.now()),
    Field('user_id', db.auth_user),
    Field('item_id', 'integer'),
    Field('details'),
    Field('table_name', requires=IS_IN_SET(('msg','auth_user','auth_group','tag','contact', 'auth_membership', 'msg_attachment','msg_tag', 'msg_group'))),
    Field('access', requires=IS_IN_SET(('create','read','update','delete'))),    
    format='%(description)s')
db.event.user_id.requires=IS_IN_DB(db, 'auth_user.id', '%(first_name)s %(last_name)s')
