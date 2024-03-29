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
    grps = db(db.auth_membership.user_id == auth.user_id).select()
    grps.exclude(lambda row: row.group_id.role == 'Admin')
    groups_query = db(db.msg_group.id > 0
                      )._select(db.msg_group.group_id, distinct=True)
    groups = db((db.auth_group.role != 'Admin')
                & (db.auth_group.id.belongs(groups_query))
                ).select(db.auth_group.role)
    groups = [group.role for group in groups]
    
    msgs = []
    contact = get_contact(auth.user)
    
    late_tag = db(db.tag.name == 'Late').select().first()    
    late_query = db(db.msg_tag.tag_id == late_tag.id)._select(db.msg_tag.msg_id)
    late = db.msg.id.belongs(late_query) if request.args(0) == 'late' else db.msg.id > 0
        
    if request.args(0) == 'trash':
        hidden = db.msg.is_hidden == True 
    else:
        hidden = db.msg.is_hidden == False
        
    if auth.has_membership('Admin'):
        messages = db((db.msg.parent_msg == 0) & late & hidden
                      ).select(db.msg.ALL, orderby=db.msg.create_time)            
               
    elif auth.has_membership('Telehealth'):
        nurse_record = db(db.contact.user_id == auth.user.id).select().first()
        msg_query_group = db(db.msg_group.id > 0)._select(db.msg_group.msg_id)
        msg_query_assigned = db(db.msg_group.assigned_by == auth.user.id
                                )._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0) & late
                      & ((db.msg.created_by == nurse_record.id)
                         | ~db.msg.id.belongs(msg_query_group)
                         | db.msg.id.belongs(msg_query_assigned)) & hidden).select()
    else:
        groups_query = db(db.auth_membership.user_id == auth.user.id
                          )._select(db.auth_membership.group_id)
        msg_query = db(db.msg_group.group_id.belongs(groups_query)
                       )._select(db.msg_group.msg_id)
        messages = db((db.msg.parent_msg == 0) & late
                      & (db.msg.id.belongs(msg_query)
                         | (db.msg.created_by == contact.id)) & hidden).select()
        
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
        comment = db((db.msg.parent_msg == message.id) & 
                     (db.msg.is_hidden == False)
                    ).select(orderby= ~db.msg.create_time)
        msg = {}
        msg['id'] = message.id
        msg['subject'] = message.subject
        cname = []
        for elem in comment:
            if elem not in cname:
                user = elem.created_by.user_id   
                cname.append(user.first_name + ' ' + user.last_name)
        
        user = message.created_by.user_id
        name = user.first_name + ' ' + user.last_name                
        if name not in cname:
            cname.append(name)
        msg['by'] = ', '.join(cname)
        msg['is_owner'] = (True if message.created_by.id == contact.id
                           else False)
        msg['time'] = (comment[0].create_time if comment
                       else message.create_time)
        msg['content'] = (comment[0].content if comment
                          else message.content)
        msg['attachment'] = (True if db(db.msg_attachment.msg_id == message.id
                                        ).count() else False)
        msg['replied'] = (True if len(comment) else False)
        tags = db(db.msg_tag.msg_id == message.id).select()
        msg['tags'] = ' '.join(['[' + tag.tag_id.name + ']' for tag in tags])
        msg['groups'] = ' '.join([group.group_id.role.replace(' ', '_')
                                  for group in db(db.msg_group.msg_id == message
                                                  ).select()])
        
        if db((db.msg_tag.msg_id == message.id) & (db.msg_tag.tag_id == late_tag.id)).count() != 0:
            late_msgs.append(msg)
        else: msgs.append(msg)
    
    if request.args(0) == 'late':
        msgs = []
    else:        
        msgs = sorted(msgs, key=lambda msg : msg['time'], reverse=True)
                   
    return dict(my_roles=grps, contact_id=contact.id, msgs=msgs, late_msgs=late_msgs,
                json=SCRIPT('var groups=%s' % groups))

def get_contact(user):
    contact = db(db.contact.user_id == user.id).select().first()
    if not contact:
        contact = db.contact.insert(user_id=user.id, contact_type='email',
                                    contact_info=user.email)
    return contact

@auth.requires_login()
def create():
    import os
    
    form = SQLFORM.factory(db.msg,
                Field('attachment', 'upload',
                      uploadfolder=os.path.join(request.folder, 'uploads')),
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
                          details=','.join([subject, filename, `msg_id`]))
                                
        if request.vars.tags_new:
            select_tags = request.vars.tags_new.split(',')[:-1]
            for tag in select_tags:
                id = db.msg_tag.insert(msg_id=msg_id, tag_id=int(tag[4:]))
                tag_id = int(tag[4:])
                tag = db.tag[tag_id].name
                dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                                  table_name='msg_tag', access='create',
                                  details=','.join([subject, tag]))
        if request.vars.groups_new:
            select_groups = request.vars.groups_new.split(',')[:-1]
            for group in select_groups:
                id = db.msg_group.insert(msg_id=msg_id, group_id=int(group[4:]),
                                    assigned_by=auth.user.id)
                dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                                  table_name='msg_group', access='create',
                                  details=','.join([subject, group]))
        
        dbutils.log_event(db, user_id=auth.user.id, item_id=msg_id,
                          table_name='msg', access='create')
        
        session.flash = T('Message successfully created.')
        redirect(URL('index'))
    return dict(form=form, json=SCRIPT('var tags=%s; var groups=%s'
                                       % (tags, groups)))

file_types = ['pdf']

@auth.requires_login()
def read():
    if len(request.args) == 0 or not request.args(0).isdigit():
        redirect(URL('index'))
    message = db(db.msg.id == int(request.args(0))).select().first() or redirect(URL('index'))
    
    contacts = db(db.contact.user_id == auth.user.id).select()
    groups_query = db(db.msg_group.msg_id == message.id
                      )._select(db.msg_group.group_id)
    not_groups = db(~db.auth_group.id.belongs(groups_query)
                    & (db.auth_group.role != 'Admin')
                    ).select(db.auth_group.id, db.auth_group.role).json()
    groups = db(db.msg_group.msg_id == message.id
                ).select(db.msg_group.id, db.msg_group.group_id, distinct=True)
    
    tags_query = db(db.msg_tag.msg_id == message.id)._select(db.msg_tag.tag_id)
    not_tags = db(~db.tag.id.belongs(tags_query) & (db.tag.name != 'Late')
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
            attach['src'] = URL('static', 'images/' + file_type + '.png')
        elif file_type in ['png', 'jpg', 'jpg', 'gif', 'bmp']:
            attach['src'] = URL('default', 'download', args=attachment.attachment)
        else:
            attach['src'] = URL('static', 'images/binary.png')
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
                attachs=attachs, update_time=update_time, contacts=contacts,
                json=SCRIPT('var tags=%s; var groups=%s'
                            % (not_tags, not_groups)),
                id=message.id, replies=replies)

def delete():
    msg = db.msg[request.vars.id]
    parent_id = request.vars.msg_id
    contacts = db(db.contact.user_id == auth.user.id).select()

    if not(auth.has_membership('Admin') or auth.has_membership('Telehealth') or 
       contacts.find(lambda row: row.id == attachment.attach_by)):
        session.flash = 'Insufficient privileges'
        redirect(URL('default', 'user', args='not_authorized'))

    dbutils.log_event(db, user_id=auth.user.id,
                      item_id=request.vars.id, table_name='msg',
                      access='delete', details='')

    db.msg[request.vars.id] = dict(is_hidden=True)    

    if parent_id == 0:
        session.flash = 'Referral successfully deleted.'
        redirect(URL('messages', 'index'))
    else:    
        session.flash = 'Comment successfully deleted.'
        redirect(URL('messages', 'read', args=parent_id))
