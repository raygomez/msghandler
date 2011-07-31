if 0:
    from gluon.globals import *
    from gluon.html import *
    from gluon.http import *
    from gluon.sqlhtml import SQLFORM, SQLTABLE, form_factory
    session = Session()
    request = Request()
    response = Response()


@auth.requires_login()
def index():
    page = int(request.args[0]) if len(request.args) else 0
    items_per_page = 20
    limitby = (page * items_per_page, (page + 1) * items_per_page + 1)
    
    if auth.has_membership('Admin') or auth.has_membership('Telehealth'):
        events = db(db.event.id > 0).select(orderby=~db.event.timestamp,
                                            limitby=limitby)
    else:
        groups_query = db(db.auth_membership.user_id == auth.user.id
                          )._select(db.auth_membership.group_id)
        msg_query = db(db.msg_group.group_id.belongs(groups_query)
                       )._select(db.msg_group.msg_id)
        messages = db(db.msg.id.belongs(msg_query))._select(db.msg.id)
        
        events = db((db.event.user_id == auth.user.id)
                    | ((db.event.table_name=='msg')
                       & (db.event.item_id.belongs(messages)))
                    ).select(orderby=~db.event.timestamp, limitby=limitby)
    
    evnts = []
    for event in events:
        evnt = {}
        evnt['timestamp'] = event.timestamp
        if auth.user.id != event.user_id.id:
            if (auth.has_membership('Admin')
                    or auth.has_membership('Telehealth')):
                evnt['user'] = A(event.user_id.first_name + ' '
                                 + event.user_id.last_name,
                                 _href=URL('show_user', args=event.user_id.id))
            else:
                evnt['user'] = (event.user_id.first_name + ' '
                                + event.user_id.last_name)
        else: evnt['user'] = 'You'
        evnt['item'] = db[event.table_name][event.item_id]
        evnt['details'] = event.details
        evnt['table'] = event.table_name
        evnt['access'] = event.access
        evnts.append(evnt)
        
    return dict(evnts=evnts, page=page, items_per_page=items_per_page)
