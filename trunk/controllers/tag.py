def index():
    form = crud.select(db.tag, orderby=db.tag.name)
    return dict(form=form)

@auth.requires_login()
def create():
    form = crud.create(db.tag, next=URL('index'))
    if form.accepts(request.vars, session):
        response.flash = T('Successfully created %s' % form.vars.name)
    elif form.errors:
        response.flash = T('Error creating tag')
    return dict(form=form)

def read():
    record = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.read(db.tag, record=record.id)
    return dict(form=form)

@auth.requires_login()
def update():
    record = db.tag(request.args(0)) or redirect(URL('create'))
    form = crud.update(db.tag, record=record.id,
                       message=T('Successfully updated %s' % (record.name)))
    return dict(form=form)

@auth.requires_login()
def delete():
    record = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.delete(db.tag, record_id=record.id, next=URL('index'),
                       message=T('Successfully deleted %s' % (record.name)))
    return dict(form=form)