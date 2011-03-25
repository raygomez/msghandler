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
def create_user():

    groups = db().select(db.auth_group.id, db.auth_group.role, orderby=db.auth_group.role).json()
    
    form = SQLFORM.factory(db.auth_user, 
        Field('password_again', requires=IS_EQUAL_TO(request.vars.password, error_message='Passwords do not match.')),
        Field('groups', label='Search groups'),  
        hidden=dict(groups_new=None),
        table_name='user')

    form.element(_name='groups')['_onkeyup']="showgroups()" 
    form.element(_name='groups')['_autocomplete']='off' 
    form[0].insert(5, TR(TD(LABEL('Groups'), _class='w2p_fl'),TD(_id='tr-groups-new')))
    form[0].insert(7, TR(TD(),TD(DIV(_id='new-groups'))))
    
    td = TABLE(TR())
    form.element('#tr-groups-new').append(td)
    
    if form.accepts(request.vars, session):
        user_id = db.auth_user.insert(**db.auth_user._filter_fields(form.vars))
        if request.vars.groups_new:
            select_groups = request.vars.groups_new.split(',')[:-1]
            for group in select_groups:
                db.auth_membership.insert(user_id=user_id, group_id=int(group))             
        session.flash = T('User successfully added.')
        redirect(URL('index'))    
        
    return dict(form = form,json=SCRIPT('var groups=%s' % groups))

@auth.requires_login()     
def show_message():
    message = db.msg(request.args(0)) or redirect(URL('index'))    
    attachments = db(db.msg_attachment.msg_id == message.id).select(orderby=db.msg_attachment.attach_time)
    tags = db(db.msg_tag.msg_id == message.id).select(orderby=db.msg_tag.tag_time)
    
    for field in db.msg.fields:
        if field is not 'id':
            db.msg[field].default = message[field]

    tags_query = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id)
    not_tags = db(~db.tag.id.belongs(tags_query)).select(db.tag.id, db.tag.name).json()
    tags = db(db.msg_tag.msg_id == message.id).select(db.msg_tag.id, db.msg_tag.tag_id, distinct=True)
        
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
    td = TABLE(TR())

    tags_new = ''

    for i in range(len(tags)): 
        td[0].append(TD(_class = 'top-td'))
        td[0][i].append(SPAN(tags[i].tag_id.name))
        td[0][i].append(IMG(_src=URL('static', 'images/delete.png'), _hidden=True, 
                        _class='tags-add', _id='imgt'+`tags[i].id`, _name=tags[i].tag_id.name))
        tags_new  = `tags[i].id` +','+ tags_new
    
    form.element('#tr-tags-new').append(td)
       
    if form.accepts(request.vars, session):
        db(db.msg.id == message.id).update(**db.msg._filter_fields(form.vars))
        form.vars.msg_id = message.id
        if request.vars.tags_new:
            tags_before = set(tags_new.split(',')[:-1])
            select_tags = set(request.vars.tags_new.split(',')[:-1])
           
            to_delete = tags_before.difference(select_tags)
            to_insert = select_tags.difference(tags_before)
            
            for tag in to_delete:
                del db.msg_tag[int(tag)]
            for tag in to_insert:
                db.msg_tag.insert(msg_id=message.id, tag_id=int(tag))
                 
        session.flash = T('Message successfully updated.')
        redirect(URL('show_message', args=message.id))    
        response.flash = 'Message updated.'
    
    return dict(form=form, attachments=attachments, id=message.id, json=SCRIPT('var tags=%s' % not_tags))
    
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

    td = TABLE(TR())
    form.element('#tr-tags-new').append(td)

    tags = db(db.tag.id > 0).select(db.tag.id, db.tag.name).json()
    
    if form.accepts(request.vars, session):
        msg_id = db.msg.insert(**db.msg._filter_fields(form.vars))
        form.vars.msg_id = msg_id
        if request.vars.attachment != '':
           db.msg_attachment.insert(**db.msg_attachment._filter_fields(form.vars))

        if request.vars.tags_new:
            select_tags = request.vars.tags_new.split(',')[:-1]
            for tag in select_tags:
                db.msg_tag.insert(msg_id=msg_id, tag_id=int(tag))             
        
        session.flash = T('Message successfully created.')
        redirect(URL('show_message', args=msg_id))
        
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
