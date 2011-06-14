dbutils = local_import('utils.dbutils')

@auth.requires_login()
def index():
    if auth.has_membership('Admin') or auth.has_membership('Telehealth'):
        users = db(db.auth_user.id > 0).select()
    else:
        groups_query = db(db.auth_membership.user_id == auth.user.id
                          )._select(db.auth_membership.group_id)
        users_query = db(db.auth_membership.group_id.belongs(groups_query)
                         )._select(db.auth_membership.user_id)
        users = db((db.auth_user.id != auth.user.id)
                   & (db.auth_user.id.belongs(users_query))).select()
    
    usrs = []
    for user in users:
        usr = {}
        usr['id'] = user.id
        usr['fname'] = user.first_name
        usr['lname'] = user.last_name        
        usr['email'] = user.email
        groups = db(db.auth_membership.user_id == user.id).select()
        grps = ''
        for group in groups:
            if group.group_id.role != 'Admin':
                grps = grps + ' ['+group.group_id.role+']'
        usr['groups'] = grps
        usrs.append(usr)
    return dict(users=users, usrs=usrs)

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def read():
    user = db.auth_user(request.args(0)) or redirect(URL('index'))
    groups = db(db.auth_membership.user_id == user.id).select()
    contacts = db(db.contact.user_id == user.id).select()
    
    for field in db.auth_user.fields:
        db.auth_user[field].default = user[field]
    
    groups_query = db(db.auth_membership.user_id == user.id
                      )._select(db.auth_membership.group_id)
    not_groups = db(~db.auth_group.id.belongs(groups_query)
                    ).select(db.auth_group.id, db.auth_group.role).json()
    
    groups = db(db.auth_membership.user_id == user.id
                ).select(db.auth_membership.id, db.auth_membership.group_id,
                         distinct=True)
    groups.exclude(lambda row: row.group_id.role == 'Admin')
    
    db.auth_user.email.writable = False
    db.auth_user.username.writable = False
    db.auth_user.password.writable = False
    form = SQLFORM.factory(db.auth_user,
                Field('groups', label='Search Groups'),
                hidden=dict(groups_new=None))
    form.element(_name='groups')['_autocomplete'] = 'off'
    
    if form.accepts(request.vars, session):
        last_name = request.vars.last_name
        first_name = request.vars.first_name
        
        details = []
        if last_name != user.last_name:
            details.append('last name changed from ' + user.last_name
                           + ' to ' + last_name)
        if first_name != user.first_name:
            details.append('first name changed from ' + user.first_name
                           + ' to ' + first_name)
        
        details = ', '.join(details)
        
        dbutils.log_event(db, details=details, user_id=auth.user.id,
                          item_id=user.id, table_name='auth_user',
                          access='update')
        db(db.auth_user.id == user.id
           ).update(**db.auth_user._filter_fields(form.vars))
        
        session.flash = T('User successfully updated.')
        redirect(URL('users'))
    
    return dict(form=form, groups=groups, id=user.id, contacts=contacts,
                json=SCRIPT('var groups=%s' % not_groups))

@auth.requires_login()
def create():

    groups = db(db.auth_group.role != 'Admin'
                ).select(db.auth_group.id, db.auth_group.role,
                         orderby=db.auth_group.role).json()
        
    form = SQLFORM.factory(db.auth_user,
                Field('password_again', 'password',
                      requires=IS_EQUAL_TO(request.vars.password,
                            error_message='Passwords do not match.')),
                Field('groups', label='Search groups'),
                hidden=dict(groups_new=None),
                table_name='user')
    
    form.element(_name='groups')['_onkeyup'] = "showgroups()"
    form.element(_name='groups')['_autocomplete'] = 'off'

    if form.accepts(request.vars, session):
        id = db.auth_user.insert(**db.auth_user._filter_fields(form.vars))
        db.contact.insert(user_id=id, contact_type='email',
                          contact_info=form.vars.email,
                name=form.vars.first_name + ' ' + form.vars.last_name)
        if request.vars.groups_new:
            insert_groups(request.vars.groups_new.split(',')[:-1],id)
        dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                          table_name='auth_user', access='create')
        session.flash = T('User successfully added.')
        redirect(URL('index'))
        
    return dict(form=form, json=SCRIPT('var groups=%s' % groups))

@auth.requires_membership('Admin')
def delete():
    id = request.vars.id
    email = db.auth_user[id].email
    dbutils.log_event(db, details=email, user_id=auth.user.id, item_id=id,
                      table_name='auth_user', access='delete')
    del db.auth_user[request.vars.id]
    return ''
