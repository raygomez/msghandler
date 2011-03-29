"""
Run me using
    python web2py.py -S msghandler -M -N
        -R applications/msghandler/private/update_late.py
"""

import datetime

#late_id = db(db.tag.name=='Late').select(db.tag.id).as_list()[0].values()
#print late_id

#cond_all = db(db.msg_tag.tag_id.belongs(late_id))._select(db.msg.ALL)
#print cond_all
## condition to filter out messages already tagged as late

cond_time = (db.msg.create_time <
                (datetime.datetime.now()-datetime.timedelta(minutes=5))
            )
filt_id = db(db.msg.parent_msg>0).select(
                db.msg.parent_msg,
                distinct=True
            ).as_list()[0].values()

print [row.id for row in db((db.msg.parent_msg>0)
              & cond_time).select(
                groupby=db.msg.parent_msg,
                orderby=~db.msg.create_time)
        ]

print [row.id for row in db((db.msg.parent_msg==0)
              & ~db.msg.id.belongs(filt_id)
            ).select()
        ]