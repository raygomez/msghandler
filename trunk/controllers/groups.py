@auth.requires_login()
def index():
    groups = db(db.auth_group.role != 'Admin'
                ).select(orderby=~db.auth_group.id)
    return dict(groups=groups)
