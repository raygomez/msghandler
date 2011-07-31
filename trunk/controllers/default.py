# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

if 0:
    from gluon.globals import *
    from gluon.html import *
    from gluon.http import *
    from gluon.sqlhtml import SQLFORM, SQLTABLE, form_factory
    session = Session()
    request = Request()
    response = Response()


dbutils = local_import('utils.dbutils')

@auth.requires_login()
def index():
    redirect(URL('messages', 'index'))
    return dict()

@auth.requires_login()
def sidebar():
    late = db(db.tag.name == 'Late').select().first()
    late_count = db(db.msg_tag.tag_id == late.id).count()
    return dict(late_count=late_count)


@auth.requires_login()
def insert_ajax():
    id = int(request.vars.id)
    second_id = int(request.vars.group[1:])
    
    if request.vars.table == 'user_group':
        membership_id = db.auth_membership.insert(user_id=id,
                                                  group_id=second_id)
        user = db.auth_user[id].email
        group = db.auth_group[second_id].role
        dbutils.log_event(db, user_id=auth.user.id, item_id=membership_id,
                          table_name='auth_membership', access='create',
                          details=','.join([user,group,`id`]))
    elif request.vars.table == 'msg_group': 
        msg_group_id = db.msg_group.insert(msg_id=id, group_id=second_id,
                                           assigned_by=auth.user.id)
        subject = db.msg[id].subject
        group = db.auth_group[second_id].role
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_group_id,
                          table_name='msg_group', access='create',
                          details=','.join([subject,group,`id`]))
    elif request.vars.table =='msg_tag':
        msg_tag_id = db.msg_tag.insert(msg_id=id, tag_id=second_id)
        subject = db.msg[id].subject
        tag = db.tag[second_id].name
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_tag_id,
                          table_name='msg_tag', access='create',
                          details=','.join([subject,tag,`id`]))

@auth.requires_login()
def delete_ajax():
    id = int(request.vars.id)
    second_id = int(request.vars.group)
    
    if request.vars.table == 'user_group':
        membership_id = db((db.auth_membership.group_id == second_id)
                           & (db.auth_membership.user_id == id)
                           ).select().first().id
        user = db.auth_user[id].email
        group = db.auth_group[second_id].role
        
        db((db.auth_membership.group_id == second_id)
           & (db.auth_membership.user_id == id)).delete()
        dbutils.log_event(db, user_id=auth.user.id, item_id=membership_id,
                          table_name='auth_membership', access='delete',
                          details=','.join([user,group,`id`]))
    elif request.vars.table =='msg_group':
        msg_group_id = db((db.msg_group.group_id == second_id)
                          & (db.msg_group.msg_id == id)).select().first().id
        subject = db.msg[id].subject
        group = db.auth_group[second_id].role
        
        db((db.msg_group.group_id == second_id)
           & (db.msg_group.msg_id == id)).delete()
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_group_id,
                          table_name='msg_group', access='delete',
                          details=','.join([subject,group,`id`]))
    elif request.vars.table =='msg_tag':
        msg_tag_id = db((db.msg_tag.tag_id == second_id)
                        & (db.msg_tag.msg_id == id)).select().first().id
        subject = db.msg[id].subject
        tag = db.tag[second_id].name
        
        db((db.msg_tag.tag_id == second_id)
           & (db.msg_tag.msg_id == id)).delete()
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_tag_id,
                          table_name='msg_tag', access='delete',
                          details=','.join([subject,tag,`id`]))        

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def contacts():
    users = db(db.auth_user.id > 0).select(orderby=~db.auth_user.id)
    contacts = db(db.contact.id > 0).select(orderby=~db.contact.id)
    return dict(contacts=contacts, users=users)

@auth.requires_login()
def data():
    return dict(form=crud())

@auth.requires_login()
def delete_attach():    
    session.flash = T('Attachment successfully deleted.')
    db(db.msg_attachment.id==request.args(0)).delete()
    redirect(URL(f='show_message', args=request.args(1)))

def user():
    return dict(form=auth())

@auth.requires_login()
def download():
    return response.download(request,db)

@auth.requires_login()
def call():
    session.forget()
    return service()
