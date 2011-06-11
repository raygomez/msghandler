dbutils = local_import('utils.dbutils')

@auth.requires_login()
def index():
    groups = db(db.auth_group.role != 'Admin'
                ).select(orderby=~db.auth_group.id)
    return dict(groups=groups)
    
    
@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def create():
    groups = db(db.auth_group.role == request.vars.role).select()
    
    if len(groups) == 0:
        id = db.auth_group.insert(**request.vars)
        dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                          table_name='auth_group', access='create',
                          details=request.vars.role)
        return `id`
    else: return '0'
    
@auth.requires_membership('Admin')
def delete():
    id = request.vars.id
    role = db.auth_group[id].role
    
    del db.auth_group[id]
    dbutils.log_event(db, details=role, user_id=auth.user.id, item_id=id,
                      table_name='auth_group', access='delete')
    return ''
