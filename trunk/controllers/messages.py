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
                user = elem.created_by.user_id   
                cname.append(user.first_name + ' ' + user.last_name)
        
        user = message.created_by.user_id
        name = user.first_name + ' ' + user.last_name                
        if name not in cname:
            cname.append(name)
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

def get_contact(user):
    contact =  db(db.contact.user_id==user.id).select().first()
    if not contact:
        contact = db.contact.insert(user_id=user.id, contact_type='email',
                                    contact_info=user.email)
    return contact

@auth.requires_login()
def create():
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
