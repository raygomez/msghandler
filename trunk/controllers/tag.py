dbutils = local_import('utils.dbutils')

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def index():
    tags = db(db.tag.id).select(orderby=~db.tag.id)
    return dict(tags=tags)

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def add_tag():
    tags = db(db.tag.name == request.vars.name).select()
    if len(tags) == 0:
        id = db.tag.insert(**request.vars)
        dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                          table_name='tag', access='create',
                          details=request.vars.name)
        return `id`
    else: return '0'
