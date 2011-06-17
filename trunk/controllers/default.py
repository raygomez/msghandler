# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

dbutils = local_import('utils.dbutils')

@auth.requires_login()
def sidebar():
    late = db(db.tag.name == 'Late').select().first()
    late_count = db(db.msg_tag.tag_id == late.id).count()
    return dict(late_count=late_count)

@auth.requires_login()
def index():
    grps = db(db.auth_membership.user_id == auth.user_id).select()
    grps.exclude(lambda row: row.group_id.role == 'Admin')
    groups_query = db(db.msg_group.id > 0
                      )._select(db.msg_group.group_id,distinct=True)
    groups = db((db.auth_group.role != 'Admin')
                & (db.auth_group.id.belongs(groups_query))
                ).select(db.auth_group.role)
    groups = [group.role for group in groups]
    
    msgs = []
    contact = get_contact(auth.user)
    
    late_tag = db(db.tag.name == 'Late').select().first()    
    late_query = db(db.msg_tag.tag_id == late_tag.id)._select(db.msg_tag.msg_id)
    late_select = db.msg.id.belongs(late_query) if request.args(0) == 'late' else db.msg.id > 0
        
    if auth.has_membership('Admin'):
        messages = db((db.msg.parent_msg == 0) & late_select).select(db.msg.ALL,orderby=db.msg.create_time)            
       
    elif auth.has_membership('Telehealth'):     
        messages = db(db.msg.parent_msg == 0
                      ).select(db.msg.ALL, orderby=~db.msg.create_time)
    
    elif auth.has_membership('Telehealth'):
        nurse_record = db(db.contact.user_id == auth.user.id).select().first()
        msg_query_group = db(db.msg_group.id > 0)._select(db.msg_group.msg_id)
        msg_query_assigned = db(db.msg_group.assigned_by == auth.user.id
                                )._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0)
                      & ((db.msg.created_by == nurse_record.id)
                         | ~db.msg.id.belongs(msg_query_group)
                         | db.msg.id.belongs(msg_query_assigned))).select()
    else:
        groups_query = db(db.auth_membership.user_id == auth.user.id
                          )._select(db.auth_membership.group_id)
        msg_query = db(db.msg_group.group_id.belongs(groups_query)
                       )._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0)
                      & (db.msg.id.belongs(msg_query)
                         | (db.msg.created_by==contact.id))).select()
        
        users_query = db(db.auth_membership.group_id.belongs(groups_query)
                         & (db.auth_membership.user_id != auth.user.id)
                         )._select(db.auth_membership.user_id)
        users = db(db.auth_user.id.belongs(users_query)
                   ).select(db.auth_user.id, db.auth_user.first_name,
                            db.auth_user.last_name, db.auth_user.email,
                            orderby=db.auth_user.last_name)
    
    msgs = []
    late_msgs = []
    for message in messages:
        comment = db(db.msg.parent_msg == message.id
                     ).select(orderby=~db.msg.create_time)
        msg = {}
        msg['id'] = message.id
        msg['subject'] = message.subject
        cname = []
        for elem in comment:
            if elem not in cname:
                cname.append(elem.created_by.name)
        if message.created_by.name not in cname:
            cname.append(message.created_by.name)
        msg['by'] = ', '.join(cname)
        msg['is_owner'] = (True if message.created_by.id==contact.id
                           else False)
        msg['time'] = (comment[0].create_time if comment
                       else message.create_time)
        msg['content'] = (comment[0].content if comment
                          else message.content)
        msg['attachment'] = (True if db(db.msg_attachment.msg_id == message.id
                                        ).count() else False)
        msg['replied'] = (True if db(db.msg.parent_msg == message.id
                                     ).count() else False)
        tags = db(db.msg_tag.msg_id == message.id).select()
        msg['tags'] = ' '.join(['['+tag.tag_id.name+']' for tag in tags])
        msg['groups'] = ' '.join([group.group_id.role.replace(' ','_')
                                  for group in db(db.msg_group.msg_id == message
                                                  ).select()])
        
        if db((db.msg_tag.msg_id == message.id) & (db.msg_tag.tag_id == late_tag.id )).count() != 0:
            late_msgs.append(msg)
        else: msgs.append(msg)
    
    if request.args(0) == 'late':
        msgs = []
    else:        
        msgs = sorted(msgs, key=lambda msg : msg['time'], reverse=True)
                   
    return dict(my_roles=grps, contact_id=contact.id, msgs=msgs,late_msgs=late_msgs,
                json=SCRIPT('var groups=%s' % groups))

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


def insert_groups(selected, user_id):
    for group in selected:
        user = db.auth_user[user_id].email
        role = db.auth_group[int(group[4:])].role
    
        membership_id = db.auth_membership.insert(user_id=user_id, group_id=int(group[4:]))
        dbutils.log_event(db, user_id=auth.user.id, item_id=membership_id,
                          table_name='auth_membership', access='create',
                          details=','.join([user,role,`user_id`]))


@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def contacts():
    users = db(db.auth_user.id > 0).select(orderby=~db.auth_user.id)
    contacts = db(db.contact.id > 0).select(orderby=~db.contact.id)
    return dict(contacts=contacts, users=users)

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def add_contact():
    id = db.contact.insert(**request.vars)
    dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                      table_name='contact', access='create', details=','.join([request.vars.contact_type,request.vars.contact_info]))
    return `id`


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
        contact = db.contact.insert(name='%s %s'
                                        % (user.first_name, user.last_name),
                                    user_id=user.id, contact_type='email',
                                    contact_info=user.email)
    return contact

@auth.requires_login()
def create_message():
    import os
    
    form = SQLFORM.factory(db.msg,
                Field('attachment', 'upload',
                      uploadfolder=os.path.join(request.folder,'uploads')),
                Field('tags', label='Search tags'),
                Field('groups', label='Search groups'),
                hidden=dict(tags_new=None, groups_new=None),
                table_name='msg_attachment')
    form.element(_name='tags')['_onkeyup'] = "showtags()"
    form.element(_name='tags')['_autocomplete'] = 'off'    
    form.element(_name='groups')['_onkeyup'] = "showgroups()"
    form.element(_name='groups')['_autocomplete'] = 'off'
    
    tags = db(db.tag.name != 'Late').select(db.tag.id, db.tag.name).json()
    groups = db().select(db.auth_group.id, db.auth_group.role).json()
    
    if form.accepts(request.vars, session):
        contact = get_contact(auth.user)
        form.vars.created_by = contact.id
        
        msg_id = db.msg.insert(**db.msg._filter_fields(form.vars))
        form.vars.msg_id = msg_id
        subject = form.vars.subject
        if request.vars.attachment != '':
            db.msg_attachment.msg_id.default = msg_id
            db.msg_attachment.attach_by.default = contact.id
            filename = request.vars.attachment.filename
            form.vars.filename = filename
            form.vars.attachment_type = filename[filename.rindex('.') + 1:]            
            msg_attachment_id = db.msg_attachment.insert(
                                **db.msg_attachment._filter_fields(form.vars))
            dbutils.log_event(db, user_id=auth.user.id, item_id=msg_attachment_id,
                          table_name='msg_attachment', access='create',
                          details=','.join([subject,filename,`msg_id`]))
                                
        if request.vars.tags_new:
            select_tags = request.vars.tags_new.split(',')[:-1]
            for tag in select_tags:
                id = db.msg_tag.insert(msg_id=msg_id, tag_id=int(tag[4:]))
                tag_id = int(tag[4:])
                tag = db.tag[tag_id].name
                dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                                  table_name='msg_tag', access='create',
                                  details=','.join([subject,tag]))
        if request.vars.groups_new:
            select_groups = request.vars.groups_new.split(',')[:-1]
            for group in select_groups:
                id = db.msg_group.insert(msg_id=msg_id, group_id=int(group[4:]),
                                    assigned_by=auth.user.id)
                dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                                  table_name='msg_group', access='create',
                                  details=','.join([subject,group]))
        
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_id,
                          table_name='msg', access='create')
        
        session.flash = T('Message successfully created.')
        redirect(URL('index'))
    return dict(form=form, json=SCRIPT('var tags=%s; var groups=%s'
                                       % (tags,groups)))

file_types = ['pdf']

@auth.requires_login()
def read_message():
    if len(request.args) == 0 or not request.args(0).isdigit():
        redirect(URL('index'))
    message = db(db.msg.id == int(request.args(0))).select().first() or redirect(URL('index'))
    
    groups_query = db(db.msg_group.msg_id == message.id
                      )._select(db.msg_group.group_id)
    not_groups = db(~db.auth_group.id.belongs(groups_query)
                    & (db.auth_group.role != 'Admin')
                    ).select(db.auth_group.id, db.auth_group.role).json()
    groups = db(db.msg_group.msg_id == message.id
                ).select(db.msg_group.id, db.msg_group.group_id, distinct=True)
    
    tags_query = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id)
    not_tags = db(~db.tag.id.belongs(tags_query) & (db.tag.name!='Late')
                  ).select(db.tag.id, db.tag.name).json()
    tags = db(db.msg_tag.msg_id == message.id
              ).select(db.msg_tag.id, db.msg_tag.tag_id, distinct=True)
    
    attachments = db(db.msg_attachment.msg_id == message.id
                     ).select(orderby=db.msg_attachment.attach_time)
    attachs = []
    for attachment in attachments:
        attach = {}
        attach['attachment'] = attachment
        file_type = attachment.attachment[attachment.attachment.rindex('.')
                                          + 1:]
        if file_type in file_types:
            attach['src'] = URL('static','images/' + file_type + '.png')
        elif file_type in ['png','jpg','jpg','gif','bmp']:
            attach['src'] = URL('download', args=attachment.attachment)
        else:
            attach['src'] = URL('static','images/binary.png')
        attachs.append(attach)
        
    db.msg.subject.writable = db.msg.subject.readable = False
    form = SQLFORM.factory(db.msg, submit_button='Post comment')
    
    if form.accepts(request.vars, session):
        contact = get_contact(auth.user)
        form.vars.created_by = contact.id
        form.vars.parent_msg = message.id
        form.vars.subject = 'Re:'
        msg_id = db.msg.insert(**db.msg._filter_fields(form.vars))
        late = db(db.tag.name == 'Late').select().first()
        db((db.msg_tag.msg_id == message.id) & (db.msg_tag.tag_id == late.id)).delete()
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_id,
                          table_name='msg', access='create')
        
        response.flash = T('Comment successfully created.')
    
    replies = db(db.msg.parent_msg == message.id
                 ).select(orderby=db.msg.create_time)
    update_time = replies.last().create_time if replies else 0
    
    return dict(message=message, form=form, groups=groups, tags=tags,
                attachs=attachs, update_time=update_time,
                json=SCRIPT('var tags=%s; var groups=%s'
                            % (not_tags,not_groups)),
                id=message.id, replies=replies)

@auth.requires_login()
def create_attachment():
    msg_id = request.args(0)
    contact = get_contact(auth.user)
    db.msg_attachment.msg_id.default = msg_id
    db.msg_attachment.attach_by.default = contact.id
    form = SQLFORM(db.msg_attachment)
    if form.accepts(request.vars, session, dbio=False):
        filename = request.vars.attachment.filename
        form.vars.filename = filename
        form.vars.attachment_type = filename[filename.rindex('.') + 1:]
        msg_attachment_id = db.msg_attachment.insert(
                                **db.msg_attachment._filter_fields(form.vars))
        subject = db.msg[msg_id].subject
        
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_attachment_id,
                          table_name='msg_attachment', access='create',
                          details=','.join([subject,filename,msg_id]))
        redirect(URL('read_message', args=msg_id))
    return dict(form = form)

@auth.requires_login()
def call():
    session.forget()
    return service()
