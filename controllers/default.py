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
    contacts = db().select(db.contact.id, db.contact.name, orderby=db.contact.name)
    tags = db().select(db.tag.id, db.tag.name, orderby=db.tag.name)
    groups = db(db.auth_group.role != 'Admin').select(db.auth_group.id, db.auth_group.role, orderby=db.auth_group.role)
    users = db().select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name, db.auth_user.email, orderby=db.auth_user.last_name)
    msg_group = db(db.msg_group.id > 0).select()
    
    msgs = []
    
    isAdmin = False
    isTelehealth = False
    if auth.has_membership('Admin'):
        isAdmin = True
        messages = db(db.msg.parent_msg == 0).select(db.msg.ALL,orderby=~db.msg.create_time)    
        
    elif auth.has_membership('Telehealth'):     
        isTelehealth = True
        nurse_record = db(db.contact.user_id == auth.user.id).select().first()
                
        msg_query_group = db(db.msg_group.id > 0)._select(db.msg_group.msg_id)
        msg_query_assigned = db(db.msg_group.assigned_by == auth.user.id)._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0) & ((db.msg.created_by == nurse_record.id) |\
                     ~db.msg.id.belongs(msg_query_group)|\
                      db.msg.id.belongs(msg_query_assigned))).select()
    else:
        contacts = []
        groups = []
        users = []
        groups_query = db(db.auth_membership.user_id == auth.user.id)._select(db.auth_membership.group_id)
        msg_query = db(db.msg_group.group_id.belongs(groups_query))._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0) & db.msg.id.belongs(msg_query)).select()
        
        users_query = db(db.auth_membership.group_id.belongs(groups_query) & (db.auth_membership.user_id != auth.user.id))._select(db.auth_membership.user_id)
        users = db(db.auth_user.id.belongs(users_query)).select(db.auth_user.id, db.auth_user.first_name, 
                db.auth_user.last_name, db.auth_user.email, orderby=db.auth_user.last_name)
    
    contact = get_contact(auth.user)
    msgs = []
    for message in messages:
        msg = {}
        msg['id'] = message.id
        msg['subject'] = message.subject
        msg['by'] = message.created_by.name
        msg['time'] = message.create_time
        tags = db(db.msg_tag.msg_id == message.id).select()
        tg = ''
        for tag in tags:
            tg = tg + '['+tag.tag_id.name+']'
        msg['tags'] = tg
        msgs.append(msg)
                
    return dict(my_roles=grps, messages=messages, contacts=contacts, contact_id=contact.id, msg_group=msg_group,
                tags=tags, users=users, groups=groups, isAdmin=isAdmin, isTelehealth=isTelehealth, msgs=msgs)

def get_groups ():
    groups = db(db.auth_membership.user_id == auth.user.id).select()
    roles = []
    for group in groups:
        roles.append(group.group_id.id)    
    return roles

def get_message():
    db.msg.created_by.readable = db.msg.create_time.readable = True
    id = int(request.vars.id)
    return crud.read(db.msg, id)

@auth.requires_login()
def insert_ajax():
    id = int(request.vars.id)
    second_id = int(request.vars.group[1:])
    
    if request.vars.table == 'user_group': db.auth_membership.insert(user_id = id, group_id = second_id)
    elif request.vars.table == 'msg_group': db.msg_group.insert(msg_id = id, group_id = second_id, assigned_by=auth.user.id)
    elif request.vars.table =='msg_tag': 
        id = db.msg_tag.insert(msg_id = id, tag_id = second_id)
        db.event.insert(user_id=auth.user.id,item_id=id,table_name='msg_tag',access='create')


    
@auth.requires_login()
def delete_ajax():
    id = int(request.vars.id)
    second_id = int(request.vars.group)
    
    if request.vars.table == 'user_group': db((db.auth_membership.group_id == second_id) & (db.auth_membership.user_id == id)).delete()
    elif request.vars.table =='msg_group': db((db.msg_group.group_id == second_id) & (db.msg_group.msg_id == id)).delete()
    elif request.vars.table =='msg_tag': db((db.msg_tag.tag_id == second_id) & (db.msg_tag.msg_id == id)).delete()
        
@auth.requires_login()
def delete_ajax_id():    
    tablename,id = request.vars.id.split('-')
    del db[tablename][id]
    
    if 'auth_' in tablename:
        tablename = tablename.replace('auth_','')
    return 'You deleted a %s' % tablename

@auth.requires_login()
def create_user():
    groups = db(db.auth_group.role != 'Admin').select(db.auth_group.id, db.auth_group.role, orderby=db.auth_group.role).json()
    
    form = SQLFORM.factory(db.auth_user, 
        Field('password_again', 'password', requires=IS_EQUAL_TO(request.vars.password, error_message='Passwords do not match.')),
        Field('groups', label='Search groups'),  
        hidden=dict(groups_new=None),
        table_name='user')

    form.element(_name='groups')['_onkeyup']="showgroups()" 
    form.element(_name='groups')['_autocomplete']='off' 
    form[0].insert(5, TR(TD(LABEL('Groups'), _class='w2p_fl'),TD(TABLE(TR()), _id='tr-groups-new')))
    form[0].insert(7, TR(TD(),TD(DIV(_id='new-groups'))))
    
    if form.accepts(request.vars, session):
        id = db.auth_user.insert(**db.auth_user._filter_fields(form.vars))
        if request.vars.groups_new:
            insert_groups(request.vars.groups_new.split(',')[:-1],id)
        db.event.insert(user_id=auth.user.id,item_id=id,table_name='auth_user',access='create')
        session.flash = T('User successfully added.')
        redirect(URL('users'))    

    return dict(form = form,json=SCRIPT('var groups=%s' % groups))

def insert_groups(selected, user_id):
    for group in selected:     
        db.auth_membership.insert(user_id=user_id, group_id=int(group[4:]))

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def show_user():
    user = db.auth_user(request.args(0)) or redirect(URL('index'))    
    groups = db(db.auth_membership.user_id == user.id).select()
    
    for field in db.auth_user.fields:
        db.auth_user[field].default = user[field]

    groups_query = db(db.auth_membership.user_id == user.id)._select(db.auth_membership.group_id)
    not_groups = db(~db.auth_group.id.belongs(groups_query)).select(db.auth_group.id, db.auth_group.role).json()
        
    groups = db(db.auth_membership.user_id == user.id).select(db.auth_membership.id, db.auth_membership.group_id, distinct=True)
    groups.exclude(lambda row: row.group_id.role == 'Admin')
    
    db.auth_user.email.writable=False
    db.auth_user.password.writable=False
    form = SQLFORM.factory(db.auth_user, 
        Field('groups', label='Search Groups'),  
        hidden=dict(groups_new=None))
    form.element(_name='groups')['_autocomplete']='off' 
    
    if form.accepts(request.vars, session):        
        last_name = request.vars.last_name
        first_name = request.vars.first_name
        
        details = []
        if last_name != user.last_name: details.append('last name changed from ' + user.last_name + ' to ' + last_name)
        if first_name != user.first_name: details.append('first name changed from ' + user.first_name + ' to ' + first_name)
        
        details = ', '.join(details)        
        
        db.event.insert(details=details,user_id=auth.user.id,item_id=user.id,table_name='auth_user',access='update')
        db(db.auth_user.id == user.id).update(**db.auth_user._filter_fields(form.vars))
        
        session.flash = T('User successfully updated.')
        redirect(URL('users'))    
    
    return dict(form=form, groups=groups, id=user.id, json=SCRIPT('var groups=%s' % not_groups))

@auth.requires_login()
def events():
    if auth.has_membership('Admin') or auth.has_membership('Telehealth'):
        events = db(db.event.id > 0).select(orderby=~db.event.timestamp)
        evnts = []
        for event in events:
            evnt = {}
            evnt['timestamp'] = event.timestamp
            evnt['user'] = A(event.user_id.first_name + ' ' + event.user_id.last_name, _href=URL('show_user', args=event.user_id.id)) if auth.user.id != event.user_id.id else 'You'
            evnt['item'] = db[event.table_name][event.item_id]
            evnt['details'] = event.details
            evnt['table'] = event.table_name
            evnt['access'] = event.access
            evnts.append(evnt)
    else: events = db(db.event.user_id == auth.user.id).select(orderby=~db.event.timestamp)
        
    return dict(events=events, evnts=evnts)
    
@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def groups():
    groups = db(db.auth_group.role != 'Admin').select(orderby=~db.auth_group.id)
    return dict(groups=groups)

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def add_group():
    groups  = db(db.auth_group.role == request.vars.role).select()
    
    if len(groups) == 0:
        id = db.auth_group.insert(**request.vars)
        db.event.insert(user_id=auth.user.id,item_id=id,table_name='auth_group',access='create')
        return `id`
    else: return '0'
    
@auth.requires_membership('Admin')
def del_group():
    id = request.vars.id
    role = db.auth_group[id].role
    
    del db.auth_group[id]
    db.event.insert(details=role,user_id=auth.user.id,item_id=id,table_name='auth_group',access='delete')
    return ''

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def update_group():
    id = request.vars.id
    role = request.vars.role
    description = request.vars.description
    
    others = db((db.auth_group.role == role) & (db.auth_group.id != id)).select()
    if len(others) == 0:
        group = db.auth_group[id]
        
        details = []
        if role != group.role: details.append('role changed from ' + group.role + ' to ' + role)
        if description != group.description: details.append('description changed from ' + group.description + ' to ' + description)
        
        details = ', '.join(details)        
        
        db.event.insert(details=details,user_id=auth.user.id,item_id=id,table_name='auth_group',access='update')
        db.auth_group[id] = dict(role=role,description=description, user_id=auth.user.id)
        return '0'
    else: return db(db.auth_group.id == id).select().json()

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def tags():
    tags = db(db.tag.id).select(orderby=~db.tag.id)
    return dict(tags=tags)

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def add_tag():
    tags = db(db.tag.name == request.vars.name).select()
    if len(tags) == 0:
        id = db.tag.insert(**request.vars)
        db.event.insert(user_id=auth.user.id,item_id=id,table_name='tag',access='create')
        return `id`
    else: return '0'
    
@auth.requires_membership('Admin')
def del_tag():
    id = request.vars.id
    name = db.tag[id].name
    del db.tag[id]
    db.event.insert(details=name,user_id=auth.user.id,item_id=id,table_name='tag',access='delete')
    return ''

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def update_tag():
    id = request.vars.id
    name = request.vars.name
    description = request.vars.description
    
    others = db((db.tag.name == name) & (db.tag.id != id)).select()
    if len(others) == 0:
        tag = db.tag[id]
        
        details = []
        if name != tag.name: details.append('name changed from ' + tag.name + ' to ' + name)
        if description != tag.description: details.append('description changed from ' + tag.description + ' to ' + description)
        
        details = ', '.join(details)        
        
        db.event.insert(details=details,user_id=auth.user.id,item_id=id,table_name='tag',access='update')
        db.tag[id] = dict(name=name,description=description)
        return '0'
    else: return db(db.tag.id == id).select().json()

@auth.requires_login()
def users():
    if auth.has_membership('Admin') or auth.has_membership('Telehealth') :
        users = db(db.auth_user.id != auth.user.id ).select()
    else:
        groups_query = db(db.auth_membership.user_id == auth.user.id)._select(db.auth_membership.group_id)    
        users_query = db(db.auth_membership.group_id.belongs(groups_query))._select(db.auth_membership.user_id)
        users = db((db.auth_user.id != auth.user.id) & (db.auth_user.id.belongs(users_query))).select()
    
    usrs = []
    for user in users:
        usr = {};
        usr['id'] = user.id
        usr['name'] = user.first_name + ' ' + user.last_name
        usr['email'] = user.email
        groups = db(db.auth_membership.user_id == user.id).select()
        grps = ''
        for group in groups:
            if group.group_id.role != 'Admin':
                grps = grps + ' ['+group.group_id.role+']'
        usr['groups'] = grps    
        usrs.append(usr)
    return dict(users=users,usrs=usrs)

@auth.requires_membership('Admin')
def del_user():
    id = request.vars.id
    email = db.auth_user[id].email
    db.event.insert(details=email,user_id=auth.user.id,item_id=id,table_name='auth_user',access='delete')
    del db.auth_user[request.vars.id]
    return ''

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def contacts():
    users = db(db.auth_user.id > 0).select(orderby=~db.auth_user.id)
    contacts = db(db.contact.id > 0).select(orderby=~db.contact.id)
    return dict(contacts=contacts,users=users)

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def add_contact():
    id = db.contact.insert(**request.vars)
    db.event.insert(user_id=auth.user.id,item_id=id,table_name='contact',access='create')    
    return `id`

@auth.requires_membership('Admin')
def del_contact():
    name = db.contact[request.vars.id].name
    db.event.insert(details=name,user_id=auth.user.id,item_id=request.vars.id,table_name='contact',access='delete')
    del db.contact[request.vars.id]
    return ''

@auth.requires(auth.has_membership('Admin') or auth.has_membership('Telehealth'))
def update_contact():
    id = request.vars.id
    name = request.vars.name
    user_id = request.vars.user_id if request.vars.user_id != '' else None
    contact_type= request.vars.contact_type
    contact_info = request.vars.contact_info        

    contact = db.contact[id]

    details = []
    if name != contact.name: details.append('name changed from ' + contact.name + ' to ' + name)
    if user_id != contact.user_id: details.append('user changed from ' + contact.user_id + ' to ' + user_id)
    if contact_type != contact.contact_type: details.append('contact type changed from ' + contact.contact_type + ' to ' + contact.contact_type)
    if contact_info != contact.contact_info: details.append('contact info changed from ' + contact.contact_info + ' to ' + contact.contact_info)
    details = ', '.join(details)        
        
    db.event.insert(details=details,user_id=auth.user.id,item_id=id,table_name='contact',access='update')
    db.contact[id] = dict(name=name,user_id=user_id, contact_type=contact_type,contact_info=contact_info)
    return ''
        
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

def get_contact(user):
    contact =  db(db.contact.user_id==user.id).select().first()
    if not contact:
        contact= db.contact.insert(name='%s %s' % (user.first_name, user.last_name), user_id=user.id, 
            contact_type='email', contact_info=user.email)
    return contact

@auth.requires_login()
def create_message():
    import os
 
    form = SQLFORM.factory(db.msg,
      Field('attachment_type'),
      Field('attachment', 'upload', uploadfolder=os.path.join(request.folder,'uploads')),
      Field('tags', label='Search tags'),
      Field('groups', label='Search groups'),
      hidden=dict(tags_new=None,groups_new=None),
      table_name='msg_attachment'
    )
    form.element(_name='tags')['_onkeyup']="showtags()" 
    form.element(_name='tags')['_autocomplete']='off' 
    form[0].insert(4, TR(TD(LABEL('Tags'), _class='w2p_fl'),TD(_id='tr-tags-new')))
    form[0].insert(6, TR(TD(),TD(DIV(_id='new-tags'))))
    form.element('#tr-tags-new').append(TABLE(TR()))

    form.element(_name='groups')['_onkeyup']="showgroups()" 
    form.element(_name='groups')['_autocomplete']='off' 
    form[0].insert(7, TR(TD(LABEL('Groups'), _class='w2p_fl'),TD(_id='tr-groups-new')))
    form[0].insert(9, TR(TD(),TD(DIV(_id='new-groups'))))
    form.element('#tr-groups-new').append(TABLE(TR()))
    
    tags = db().select(db.tag.id, db.tag.name).json()
    groups = db().select(db.auth_group.id, db.auth_group.role).json()
    
    if form.accepts(request.vars, session):
        contact = get_contact(auth.user)
        form.vars.created_by = contact.id
        
        msg_id = db.msg.insert(**db.msg._filter_fields(form.vars))
        form.vars.msg_id = msg_id
        if request.vars.attachment != '':
           db.msg_attachment.insert(**db.msg_attachment._filter_fields(form.vars))
        if request.vars.tags_new:
            select_tags = request.vars.tags_new.split(',')[:-1]
            for tag in select_tags:
                id = db.msg_tag.insert(msg_id=msg_id, tag_id=int(tag[4:]))
                db.event.insert(user_id=auth.user.id,item_id=id,table_name='msg_tag',access='create')
        if request.vars.groups_new:
            select_groups = request.vars.groups_new.split(',')[:-1]
            for group in select_groups:
                db.msg_group.insert(msg_id=msg_id, group_id=int(group[4:]), assigned_by=auth.user.id)        

        db.event.insert(user_id=auth.user.id,item_id=msg_id,table_name='msg',access='create')
                
        session.flash = T('Message successfully created.')
        redirect(URL('index'))
    return dict(form=form, json=SCRIPT('var tags=%s; var groups=%s' % (tags,groups)))

@auth.requires_login()
def read_message():
    message = db(db.msg.id == int(request.args(0))).select().first() or redirect(URL('index'))
    attachments = db(db.msg_attachment.msg_id == message.id).select(orderby=db.msg_attachment.attach_time)
    
    groups_query = db(db.msg_group.msg_id == message.id)._select(db.msg_group.group_id)
    not_groups = db(~db.auth_group.id.belongs(groups_query) & (db.auth_group.role != 'Admin')).select(db.auth_group.id, db.auth_group.role).json()
    groups = db(db.msg_group.msg_id == message.id).select(db.msg_group.id, db.msg_group.group_id, distinct=True)

    tags_query = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id)
    not_tags = db(~db.tag.id.belongs(tags_query)).select(db.tag.id, db.tag.name).json()
    tags = db(db.msg_tag.msg_id == message.id).select(db.msg_tag.id, db.msg_tag.tag_id, distinct=True)
    
    db.msg.subject.writable = db.msg.subject.readable = False
    form = SQLFORM.factory(db.msg)

    if form.accepts(request.vars, session):
        contact = get_contact(auth.user)
        form.vars.created_by = contact.id
        form.vars.parent_msg = message.id   
        form.vars.subject = 'Re:'   
        msg_id = db.msg.insert(**db.msg._filter_fields(form.vars))
        #db.event.insert(description='commented on the message %s' % (message.subject), user_id=auth.user.id)
        response.flash = T('Comment successfully created.')

    replies = db(db.msg.parent_msg == message.id).select(orderby=db.msg.create_time)

    return dict(message=message, form=form, attachments=attachments, groups=groups, tags=tags, \
        json=SCRIPT('var tags=%s; var groups=%s' % (not_tags,not_groups)), id=message.id, replies=replies)
    
@auth.requires_login()
def create_attachment():
    db.msg_attachment.msg_id.default = request.args(0)
    form = crud.create(db.msg_attachment, next=URL('read_message', args=request.args(0)))
    return dict(form = form)
   
@auth.requires_login()    
def call():
    session.forget()
    return service()
