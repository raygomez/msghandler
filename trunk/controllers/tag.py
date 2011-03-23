def index():
    form = crud.select(db.tag, orderby=db.tag.name)
    return dict(form=form)

@auth.requires_login()
def create():
    form = crud.create(db.tag, next=URL('index'))
    if form.accepts(request.vars, session):
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    return dict(form=form)

def read():
    record = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.read(db.tag, record_id=record.id)
    return dict(form=form)

@auth.requires_login()
def update():
    record = db.tag(request.args(0)) or redirect(URL('create'))
    form = crud.update(db.tag, record_id=record.id)
    return dict(form=form)

@auth.requires_login()
def delete():
    record = db.tag(request.args(0)) or redirect(URL('index'))
    form = crud.delete(db.tag, record_id=request.args(0), next=URL('index'), message='succesful')
    return dict(form=form)