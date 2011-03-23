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
        my_roles.append(grp.group_id.role)

    groups = db().select(db.auth_group.id, db.auth_group.role, orderby=db.auth_group.role)
    messages = db().select(db.msg.id, db.msg.subject, db.msg.created_by, orderby=db.msg.subject)
    contacts = db().select(db.contact.id, db.contact.name, orderby=db.contact.name)
    tags = db().select(db.tag.id, db.tag.name, orderby=db.tag.name)
    users = db().select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name, db.auth_user.email, orderby=db.auth_user.last_name)
    
    return dict(my_roles=my_roles, messages=messages, contacts=contacts, tags=tags, users=users, groups=groups)

@auth.requires_login()     
def show_message():
    message = db.msg(request.args(0)) or redirect(URL('index'))    

    attachments = db(db.msg_attachment.msg_id == message.id).select(orderby=db.msg_attachment.attach_time)
    tags = db(db.msg_tag.msg_id == message.id).select(orderby=db.msg_tag.tag_time)
    
    input = INPUT(_id='keyword', _name='keyword', _autocomplete='off', _onkeyup="ajax('%s', ['keyword'], 'working')" 
                % URL(r=request,f='bg_find', args=request.args(0)))

    tr = [TD(
                SPAN(row.tag_id.name), 
                SPAN(IMG(_src=URL(c='static',f='images', args='delete.png' )), _hidden=True, _id='tag%d' % row.id,  
                      _onclick="ajax('%s', [''], ':eval')" % (URL(r=request,f='del_tag', args=row.id))),
                    _id='div-tag%d' % row.id, _class='span-div-tags') for row in tags ]
    
    form = crud.update(db.msg, message)
    form[0].insert(4, TR(TD(LABEL('Tags')), TD(TABLE(TR(tr, _id='tr-tags')))))
    form[0].insert(5, TR(TD(LABEL('Search tags')),TD(input, _id='tr-tags-search')))
    form[0].insert(6, TR(TD(),TD(DIV(_id='working'))))
    
    if form.accepts(request.vars, session):
       response.flash = 'Message updated.'
    
    return dict(form=form, attachments=attachments, id=message.id)

@auth.requires_login()
def del_tag():
    del db.msg_tag[int(request.args(0))]
    return "$('#div-tag%s').fadeOut('fast', function() { $(this).remove(); });$('#keyword').keyup(); " % request.args(0)

@auth.requires_login()
def add_tag():    

    msg_id = int(request.args(0))
    tag_id = int(request.args(1))
    row = db.tag[tag_id]
    
    dup = db.msg_tag((db.msg_tag.msg_id == msg_id) & (db.msg_tag.tag_id == tag_id ))
    
    if dup is not None : return ''
    
    msg_tag_id = db.msg_tag.insert(msg_id=msg_id, tag_id=tag_id)
    td = TD(
                SPAN(row.name), 
                SPAN(IMG(_src=URL(c='static',f='images', args='delete.png' )), _hidden=True, _id='tag%d' % msg_tag_id, 
                      _onclick="ajax('%s', [''], ':eval')" % URL(r=request,f='del_tag', args=msg_tag_id)),
                _id='div-tag%d' % msg_tag_id, _class='span-div-tags')            
                
    return "$('#div-untag%s').fadeOut(function() { $(this).remove();});$('#tr-tags').append('%s')" % (request.args(1), td)

@auth.requires_login()
def bg_find():
    if request.vars.keyword.lower():
        pattern = '%' + request.vars.keyword.lower() + '%'
    else:
        pattern = ''

    message = db.msg(request.args(0))

    tags1 = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id, orderby=db.msg_tag.tag_time)
    tags = db(db.tag.name.lower().like(pattern) & ~db.tag.id.belongs(tags1)).select(orderby=db.tag.name, limitby=(0,5))

    items = [DIV(INPUT(_type='checkbox', _name=row.name, 
            _onclick="ajax('%s', [''], ':eval')" % URL(r=request,f='add_tag', args=(request.args(0),row.id))),
            LABEL(row.name), _id='div-untag%d' % row.id) for row in tags]
    return DIV(*items)
    
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

#form[0] is the table in the form
#form[0][i] is the i-th row
#form[0][i][1] is the 2nd column of the i-th row
#form[0][i][1][0] is the INPUT inside that
#form[0]['_class'] is the class attribute of the table
#form[0][i][1][0]['_name'] is the name attribute of the INPUT
#form.element(_name='email')['_class'] is the class attribute of the
#element with attribute name=='email'
 
    form = SQLFORM.factory(db.msg,
      Field('attachment_type'),
      Field('attachment', 'upload', uploadfolder=os.path.join(request.folder,'uploads')),
      Field('tags', label='Search tags'),
      hidden=dict(tags_new=None),
      table_name='msg_attachment'
    )
    form.element(_name='tags')['_onkeyup']="showtags()" 
    form.element(_name='tags')['_autocomplete']='off' 
    form[0].insert(6, TR(TD(LABEL('Tags'), _class='w2p_fl'),TD(_id='tr-tags-new')))
    form[0].insert(8, TR(TD(),TD(DIV(_id='new-tags'))))
       
    tags = db(db.tag.id > 0).select(db.tag.id, db.tag.name).json()
    
    if form.accepts(request.vars, session):
        msg_id = db.msg.insert(subject=request.vars.subject, 
                content=request.vars.subject, 
                created_by=request.vars.created_by,
                create_time=request.vars.create_time)

        if request.vars.attachment != '':
           db.msg_attachment.insert(msg_id=msg_id, 
               attachment_type=request.vars.attachment_type,
               attachment= form.vars.attachment)
        if request.vars.tags_new != ',':
            select_tags = request.vars.tags_new.split(',')
            for i in range(len(select_tags)-1):
                db.msg_tag.insert(msg_id=msg_id, tag_id=int(select_tags[i]))             
        session.flash = T('Message successfully created.')
        redirect(URL(f='show_message', args=msg_id))
    
    return dict(form=form, json=SCRIPT('var tags=%s' % tags))
    
@auth.requires_login()
def create_attachment():
    """
    allows to create a simple attachment for testing
    """
    db.msg_attachment.msg_id.default = request.args(0)
    form = crud.create(db.msg_attachment, next=URL('show_message', args=request.args(0)))
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
