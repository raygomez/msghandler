"""
LATE TAGGER
  Adds the 'late' tag to messages that exceed a certain period (minutes).
  The period is [ideally] specified in the admin settings.

Run with
  python web2py.py -S msghandler -M -N
  -R applications/msghandler/private/update_late.py
OR use cron

Rules to follow:
  http://www.python.org/dev/peps/pep-0008/
  http://www.python.org/dev/peps/pep-0257/
"""

# IMPORTS START HERE ---------------------------------------------------------
# standard library imports
import datetime

# related third party imports

# local application/library specific imports

# CODE STARTS HERE -----------------------------------------------------------
late_id = db(db.tag.name=='Late').select(db.tag.id).first().id

cond_time = (db.msg.create_time <
                (datetime.datetime.now()-datetime.timedelta(minutes=5)))

qry = []

# list of child comments
# group by parent message
# get to be tagged as late
qry1 = db((db.msg.parent_msg>0) & cond_time).select(
                db.msg.parent_msg, db.msg.id, orderby=~db.msg.create_time,
                groupby=db.msg.parent_msg
            ).as_list()
for elem in qry1:
    qry.append(elem['parent_msg'])

# list messages without comments
# get to be tagged as late
qry2 = db((db.msg.parent_msg==0) & cond_time).select(
                db.msg.id, orderby=~db.msg.create_time
            ).as_list()
for elem in qry2:
    x = elem['id']
    if x not in qry:
        qry.append(x)
    
# get already tagged as late
# remove from qry
qry3 = db().select(db.msg_tag.msg_id).as_list()
for elem in qry3:
    x = elem['msg_id']
    if x in qry:
        qry.remove(x)

[db.msg_tag.insert(msg_id=elem, tag_id=late_id) for elem in qry]

# required, transaction will revert if not included
db.commit()