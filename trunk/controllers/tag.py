@auth.requires(auth.has_membership('Admin')
               or auth.has_membership('Telehealth'))
def index():
    tags = db(db.tag.id).select(orderby=~db.tag.id)
    return dict(tags=tags)
