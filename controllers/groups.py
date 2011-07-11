dbutils = local_import('utils.dbutils')

@auth.requires_login()
def index():
    groups = db(db.auth_group.role != 'Admin'
                ).select(orderby=~db.auth_group.id)
    return dict(groups=groups)
    
    
@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def create():
    groups = db(db.auth_group.role.like(request.vars.role)).select()
    
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
    
@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def update():
    id = request.vars.id
    role = request.vars.role
    description = request.vars.description
    
    others = db((db.auth_group.role == role)
                & (db.auth_group.id != id)).select()
    if len(others) == 0:
        group = db.auth_group[id]
        
        details = []
        if role != group.role:
            details.append('role changed from ' + group.role + ' to ' + role)
        if description != group.description:
            details.append('description changed from ' + group.description
                           + ' to ' + description)
        
        details = ', '.join(details)
        
        dbutils.log_event(db, details=details, user_id=auth.user.id,
                          item_id=id, table_name='auth_group',
                          access='update')
        db.auth_group[id] = dict(role=role, description=description,
                                 user_id=auth.user.id)
        return '0'
    else: return db(db.auth_group.id == id).select().json()
