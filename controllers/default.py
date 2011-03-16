# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

@auth.requires_login()
def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    #groups = db(db.auth_membership.user_id == auth.user_id).select(db.auth_membership.group_id)
    groups = db(db.auth_membership.user_id == auth.user_id).select()
    roles = []
    for group in groups:
        roles.append(group.group_id.role)

    messages = db().select(db.msg.id, db.msg.subject, db.msg.created_by, orderby=db.msg.subject)
    contacts = db().select(db.contact.id, db.contact.name, orderby=db.contact.name)
    tags = db().select(db.tag.id, db.tag.name, orderby=db.tag.name)
    
    return dict(grp=roles, messages=messages, contacts=contacts, tags=tags)
     
def show_message():
    this_message = db.msg(request.args(0)) or redirect(URL('index'))
    
    attachments = db(db.msg_attachment.msg_id == this_message.id).select(orderby=db.msg_attachment.attach_time)
    
    form = crud.update(db.msg, this_message, next=URL('index'))
    return dict(form=form, attachments=attachments,id=this_message.id)


def show_contact():
    this_contact = db.contact(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.contact, this_contact, next=URL('index'))
    return dict(form=form)

def show_tag():
    tag = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.tag, tag, next=URL('index'))
    return dict(form=form)


def data():
    return dict(form=crud())

def delete_attach():    
    session.flash = T('Attachment successfully deleted.')
    db(db.msg_attachment.id==request.args(0)).delete()
    redirect(URL(f='show_message', args=request.args(1)))
    
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)

def create_message():
    """
    allows to create a simple message for testing
    """
    form = crud.create(db.msg, next=URL('index'))
    return dict(form = form)

def create_contact():
    """
    allows to create a simple contact for testing
    """
    form = crud.create(db.contact, next=URL('index'))
    
    return dict(form = form)

def create_attachment():
    """
    allows to create a simple attachment for testing
    """
    db.msg_attachment.msg_id.default = request.args(0)
    form = crud.create(db.msg_attachment, next=URL('show_message', args=request.args(0)))
    #db.msg_attachment.msg_id.default = request.arg(0)
    return dict(form = form)


def create_tag():
    """
    allows to create a simple contact for testing
    """
    form = crud.create(db.tag, next=URL('index'))
    return dict(form = form)
    
def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()
