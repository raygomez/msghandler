if 0:
    from gluon.globals import *
    from gluon.html import *
    from gluon.http import *
    from gluon.sqlhtml import SQLFORM, SQLTABLE, form_factory
    session = Session()
    request = Request()
    response = Response()

dbutils = local_import('utils.dbutils')

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def create():
    id = db.contact.insert(**db.contact._filter_fields(request.vars))
    dbutils.log_event(db, user_id=auth.user.id, item_id=id,
                      table_name='contact', access='create', 
                      details=','.join([request.vars.contact_type,
                                        request.vars.contact_info]))
    return `id`

@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def update():
    id = request.vars.id
    contact_type = request.vars.contact_type
    contact_info = request.vars.contact_info
    
    contact = db.contact[id]    
    
    details = []
    if contact_type != contact.contact_type:
        details.append('contact type changed from ' + contact.contact_type
                       + ' to ' + contact_type)
    if contact_info != contact.contact_info:
        details.append('contact info changed from ' + contact.contact_info
                       + ' to ' + contact_info)
    details = ', '.join(details)
    
    dbutils.log_event(db, details=details, user_id=auth.user.id, item_id=id,
                      table_name='contact', access='update')
    db.contact[id] = dict(contact_type=contact_type, contact_info=contact_info)
    return ''


@auth.requires_membership('Admin')
def delete():
    contact = db.contact[request.vars.id]
    contact_type = contact.contact_type
    contact_info = contact.contact_info
    dbutils.log_event(db, user_id=auth.user.id,
                      item_id=request.vars.id, table_name='contact',
                      access='delete', details=','.join([contact_type,contact_info]))
    del db.contact[request.vars.id]
    return ''
