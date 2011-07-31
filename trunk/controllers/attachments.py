if 0:
    from gluon.globals import *
    from gluon.html import *
    from gluon.http import *
    from gluon.sqlhtml import SQLFORM, SQLTABLE, form_factory
    session = Session()
    request = Request()
    response = Response()

dbutils = local_import('utils.dbutils')

def get_contact(user):
    contact =  db(db.contact.user_id==user.id).select().first()
    return contact

@auth.requires_login()
def create():
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

        session.flash = 'File successfully attached.'
        redirect(URL('messages','read', args=msg_id))
    return dict(form = form)

def delete():
    attachment = db.msg_attachment[request.vars.id]
    contacts =  db(db.contact.user_id==auth.user.id).select()

    filename = attachment.filename
    
    if not(auth.has_membership('Admin') or auth.has_membership('Telehealth') or 
       contacts.find(lambda row: row.id==attachment.attach_by)):
        session.flash = 'Insufficient privileges'
        redirect(URL('default','user',args='not_authorized'))

    dbutils.log_event(db, user_id=auth.user.id,
                      item_id=request.vars.id, table_name='msg_attachment',
                      access='delete', details=','.join([attachment.msg_id.subject, filename,`attachment.msg_id.id`]))
    del db.msg_attachment[request.vars.id]
    session.flash = 'File successfully deleted.'
    
    redirect(URL('messages','read', args=request.vars.msg_id))
