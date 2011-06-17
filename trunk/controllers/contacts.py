dbutils = local_import('utils.dbutils')

@auth.requires_membership('Admin')
def delete():
    contact = db.contact[request.vars.id]
    name = contact.name
    contact_type = contact.contact_type
    contact_info = contact.contact_info
    dbutils.log_event(db, user_id=auth.user.id,
                      item_id=request.vars.id, table_name='contact',
                      access='delete', details=','.join([name,contact_type,contact_info]))
    del db.contact[request.vars.id]
    return ''
