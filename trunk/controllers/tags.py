dbutils = local_import('utils.dbutils')

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def index():
    tags = db(db.tag.id).select(orderby=~db.tag.id)
    return dict(tags=tags)

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def create():
    tags = db(db.tag.name == request.vars.name).select()
    if len(tags) == 0:
        id = db.tag.insert(**request.vars)
        dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                          table_name='tag', access='create',
                          details=request.vars.name)
        return `id`
    else: return '0'

@auth.requires_membership('Admin')
def delete():
    id = request.vars.id
    name = db.tag[id].name
    del db.tag[id]
    dbutils.log_event(db, details=name, user_id=auth.user.id,
                      item_id=id, table_name='tag', access='delete')
    return ''
