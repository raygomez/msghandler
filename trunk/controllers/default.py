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

    grps = db(db.auth_membership.user_id == auth.user_id).select()
    my_roles = []
    for grp in grps:
        roles.append(grp.group_id.role)

    groups = db().select(db.auth_group.id, db.auth_group.role, orderby=db.auth_group.role)
    messages = db().select(db.msg.id, db.msg.subject, db.msg.created_by, orderby=db.msg.subject)
    contacts = db().select(db.contact.id, db.contact.name, orderby=db.contact.name)
    tags = db().select(db.tag.id, db.tag.name, orderby=db.tag.name)
    users = db().select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name, db.auth_user.email, orderby=db.auth_user.last_name)
    
    return dict(my_roles=my_roles, messages=messages, contacts=contacts, tags=tags, users=users, groups=groups)

@auth.requires_login()     
def show_message():
    message = db.msg(request.args(0)) #or redirect(URL('index'))    

    attachments = db(db.msg_attachment.msg_id == message.id).select(orderby=db.msg_attachment.attach_time)
    tags = db(db.msg_tag.msg_id == message.id).select(orderby=db.msg_tag.tag_time)
    form = crud.update(db.msg, message, next=URL('index'))

    tr = [TD(
                SPAN(LABEL(row.tag_id.name),_onclick="$('#tag%d').slideToggle()" % row.id), 
                SPAN(INPUT(_type='checkbox', _name=row.tag_id.name), LABEL('Delete'), _hidden=True, _id='tag%d' % row.id, 
                      _onclick="ajax('%s', [''], ':eval')" % URL(r=request,f='del_tag', args=row.id)),
                _id='div-tag%d' % row.id)            
            for row in tags ]

    input = INPUT(_id='keyword', _name='keyword', 
        _onkeyup="ajax('%s', ['keyword'], 'working')" % URL(r=request,f='bg_find', args=request.args(0)))
    searchform = FORM(TABLE( TR(TD(LABEL('Add tag'), _class='w2p_fl'),TD(input)),  TR(TD(LABEL(''), _class='w2p_fl'),TD(DIV(_id='working') ))))
    return dict(form=form, attachments=attachments, id=message.id, tags=TR(*tr), searchform=searchform)

def del_tag():
    del db.msg_tag[int(request.args(0))]
    return "$('#div-tag%s').fadeOut(function() { $(this).remove(); })" % request.args(0)

def bg_find():
    if request.vars.keyword.lower():
        pattern = '%' + request.vars.keyword.lower() + '%'
    else:
        pattern = ''

    message = db.msg(request.args(0))

    tags1 = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id, orderby=db.msg_tag.tag_time)
    tags = db(db.tag.name.lower().like(pattern) & ~db.tag.id.belongs(tags1)).select(orderby=db.tag.name)

    items = [DIV(INPUT(_type='checkbox', _name=row.name),LABEL(row.name)) for row in tags]
    return DIV(*items)
    
@auth.requires_login()
def show_contact():
    contact = db.contact(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.contact, contact, next=URL('index'))
    return dict(form=form)

@auth.requires_login()
def show_user():
    user = db.auth_user(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.auth_user, user, next=URL('index'))
    return dict(form=form)

@auth.requires_login()
def show_group():
    group = db.auth_group(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.auth_group, group, next=URL('index'))
    return dict(form=form)
    
@auth.requires_login()
def show_tag():
    tag = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.tag, group, next=URL('index'))
    return dict(form=form)
        
@auth.requires_login()
def show_tag():
    tag = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.update(db.tag, tag, next=URL('index'))
    return dict(form=form)

@auth.requires_login()
def data():
    return dict(form=crud())

@auth.requires_login()
def delete_attach():    
    session.flash = T('Attachment successfully deleted.')
    db(db.msg_attachment.id==request.args(0)).delete()
    redirect(URL(f='show_message', args=request.args(1)))

@auth.requires_login()
def delete_tag():    
    session.flash = T('Tag successfully deleted.')
    db(db.msg_tag.id==request.args(0)).delete()
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

@auth.requires_login()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)

@auth.requires_login()
def create_message():
    """
    allows to create a simple message for testing
    """
    import os

    form = SQLFORM.factory(
      Field('subject', notnull=True),
      Field('content', 'text', notnull=True),
      Field('created_by', db.contact, requires=IS_IN_DB(db, 'contact.id', '%(name)s')),
      Field('create_time', 'datetime', notnull=True, default=datetime.now()),
      Field('attachment_type'),
      Field('attachment', 'upload', uploadfolder=os.path.join(request.folder,'uploads')),
      table_name='msg_attachment'
    )
    if form.accepts(request.vars, session):
        msg_id = db.msg.insert(subject=request.vars.subject, 
                content=request.vars.subject, 
                created_by=request.vars.created_by,
                create_time=request.vars.create_time)

        if request.vars.attachment != '':
           db.msg_attachment.insert(msg_id=msg_id, 
               attachment_type=request.vars.attachment_type,
               attachment= form.vars.attachment)

        session.flash = T('File successfully attached.')
        redirect(URL(f='show_message', args=msg_id))
    
    return dict(form = form)

@auth.requires_login()
def create_contact():
    """
    allows to create a simple contact for testing
    """
    form = crud.create(db.contact, next=URL('index'))
    
    return dict(form = form)

@auth.requires_login()
def create_tag():
    """
    allows to create a simple tag for testing
    """
    form = crud.create(db.tag, next=URL('index'))
    
    return dict(form = form)

@auth.requires_login()
def create_attachment():
    """
    allows to create a simple attachment for testing
    """
    db.msg_attachment.msg_id.default = request.args(0)
    form = crud.create(db.msg_attachment, next=URL('show_message', args=request.args(0)))
    return dict(form = form)

@auth.requires_login()
def create_tag():
    """
    allows to create a simple contact for testing
    """
    form = crud.create(db.tag, next=URL('index'))
    return dict(form = form)

@auth.requires_login()    
def create_group():
    """
    allows to create a simple contact for testing
    """
    form = crud.create(db.auth_group, next=URL('index'))
    return dict(form = form)
        
    
@auth.requires_login()    
def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()
