from re import M
from flask import (
    Flask, request, render_template, 
    redirect, url_for, flash, session,
    abort, g
)
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
import forms
import cryptography


app = Flask(__name__)
app.debug = True
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

# database entities classes

class User(db.Model):
    __tablename__ = 'users'
    # columns
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    # one-to-many To_do_list relationships
    to_do_lists = db.relationship('To_do_list', backref='User')
    
    def __repr__(self):
        return f'User {self.id}:{self.login}'


class To_do_list(db.Model):
    __tablename__ = 'to_do_lists'
    # columns
    list_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    # one-to-many Item relationships
    items = db.relationship('Item', backref='to_do_lists')
    user_id = db.Column(
        db.Integer(),
        db.ForeignKey('users.id'),
        nullable=False
    )
    
    def __repr__(self):
        return f'List {self.list_id}:{self.name}'


class Item(db.Model):
    __tablename__ = 'items'
    # columns
    item_id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    list_id = db.Column(
        db.Integer,
        db.ForeignKey('to_do_lists.list_id'),
        nullable=False
    )


@app.url_value_preprocessor
def store_value(endpoint, values):
    g.list_id = values.get('list_id', None)


@app.before_request
def before_request():
    """
    Checks if user has access for requested
    urls.
    """
    # if user loged in
    if session.get('loged_in'):
        # if url is signin or register
        print(request.endpoint)
        if request.endpoint.endswith(('signin', 'register')):
            return redirect(url_for('user_lists'))
        # if url is items
        elif request.endpoint.find('items') != -1:
            # checks if user has permission
            # to access provaided 'list_id'
            login = session.get('loged_in')
            user_data = retrieve_user_by_login(login, ['id'])
            user_id = user_data.get('id')
            list_id = g.list_id
            list_user_match = db.session.query(To_do_list).where(
                To_do_list.list_id == list_id,
                To_do_list.user_id == user_id
            ).count()

            if list_user_match == 0:
                abort(401)
                
    else:
        # if url is not signin, register or static
        if not request.endpoint.endswith(('signin', 'register', 'static')):
            return redirect(url_for('signin')) 


@app.route('/signin', methods = ['GET', 'POST'])
def signin():
    """
    Renders sigin.html page
    """

    form = forms.signin()
    dict_rend_temp = dict(
        template_name_or_list='login_register.html',
        template_add='login.html',
        form=form, 
        form_endpoint='signin', 
        label_text='Sign in',
        alt_endpoint = 'register'
    )
    
    # signin logic
    if form.validate_on_submit():
        login = form.login.data
        password = form.password.data
        
        print(login)
        print(password) 
        
        user_data = retrieve_user_by_login(login)

        # user not registered
        if not user_data:
            flash('No user with such login', 'error')
            return render_template(**dict_rend_temp)        
        
        # wrong password
        if not user_data.get('password') == password:
            flash('Wrong password', 'error')
            return render_template(**dict_rend_temp)

        # sending login session
        add_login_session(login)

        return redirect(url_for('user_lists'))

    return render_template(**dict_rend_temp)


@app.route('/signout')
def signout():
    session.pop('loged_in')
    return redirect(url_for('signin'))


def retrieve_user_by_login(login, fields=['id', 'login', 'password']):
    """
    Search for user in 'User' database
    by login.
    Returns:
    user_data : dictionary
    Consists of keys taken from 'fields' list. 
    """
    us = db.session.query(
        User.id, 
        User.login, 
        User.password
    ).where(User.login == login).all()
    
    if not us:
        return us
    
    user_data = {}
    
    if 'id' in fields:
        user_data['id'] = us[0][0]
    if 'login' in fields:
        user_data['login'] = us[0][1]
    if 'password' in fields:
        user_data['password'] = us[0][2]
    
    return user_data


@app.route('/register', methods = ['GET', 'POST'])
def register():
    """
    Renders register.html page
    """

    form = forms.register()
    dict_rend_temp = dict(
        template_name_or_list='login_register.html',
        template_add='register.html',
        form=form, 
        form_endpoint='register', 
        label_text='Register',
        alt_endpoint = 'signin'
    )
    
    # register logic
    if form.validate_on_submit():
        login = form.login.data
        password = form.password.data

        print(login, ':', password)
        user_data = retrieve_user_by_login(login)
        
        # user is already exists
        if user_data:
            flash('There is already user with such login')
            return render_template(**dict_rend_temp)
        
        us = User(login=login, password=password)

        db.session.add(us)
        db.session.commit()

        add_login_session(login)

        return redirect(url_for('user_lists'))

    return render_template(**dict_rend_temp)


def add_login_session(login):
    session.permanent = True
    session['loged_in'] = login
        

@app.route('/')
def index():
    """     
    Redirects to 'user_lists' view function
    """
    return redirect(url_for('user_lists'))


@app.route('/user', methods=['GET', 'POST'])
def user_lists():
    """
    Renders lists.html page.
    Performs new list addition,
    list removal, edit, save edits.
    """

    login = session.get('loged_in')
    user_data = retrieve_user_by_login(login, ['id'])

    form_list_holder = forms.single_list()
    form_new_list = forms.add_list()
    
    # add new list
    if form_new_list.validate_on_submit(): 
        name = form_new_list.new_list_input.data
        print(name)

        l = To_do_list(name=name, user_id=user_data.get('id'))
        db.session.add(l)
        db.session.commit()

        return redirect(url_for('user_lists'))
    # operations on a list
    elif form_list_holder.validate_on_submit():
        # edit list name 
        if form_list_holder.edit.data == True:
            todo_lists = retrieve_user_lists(user_data.get('id'))
            list_id = form_list_holder.list_id.data
            print(list_id)
            return render_template(
                'lists.html',
                form_new_list=form_new_list,
                form_list_holder=form_list_holder,
                rows=todo_lists,
                id=list_id
                )
        # save new list name
        elif form_list_holder.save.data == True:
            list_id = form_list_holder.list_id.data
            list_name = form_list_holder.list_name.data
            db.session.query(To_do_list).filter(To_do_list.list_id == list_id).\
                update({'name': list_name})
            db.session.commit()
        # open tasks of list
        elif form_list_holder.open.data == True:
            list_id = form_list_holder.list_id.data
            return redirect(url_for("items", list_id=list_id))
        # delete list
        elif form_list_holder.delete.data == True:    
            list_id = form_list_holder.list_id.data
            
            to_do_list = db.session.query(To_do_list).get(list_id)
            list_items = db.session.query(Item).\
                where(Item.list_id == to_do_list.list_id).delete()
            
            db.session.delete(to_do_list)
            db.session.commit()

        return redirect(url_for('user_lists'))

    todo_lists = retrieve_user_lists(user_data.get('id'))        
    print(todo_lists)

    return render_template(
        'lists.html',
        form_new_list=form_new_list,
        form_list_holder=form_list_holder,
        rows=todo_lists,
        id=None)
    

def retrieve_user_lists(id):
    """
    Returns user lists from 'To_do_lists' db.
    Attribute:
    id : number. User id in 'Users' db.
    Returns:
    todo_lists : list of tuples. 
    Each tuple construction is (list_id, name). 
    """
    todo_lists = db.session.query(
        To_do_list.list_id, 
        To_do_list.name
    ).where(To_do_list.user_id==id).all()
    return todo_lists


def retrieve_list_task(list_id):
    """
    Returns tasks from 'Items' db with
    'list_id' field equals list_id attribute.
    Attribute:
    list_id : number. List id in 'To_do_lists' db.
    Returns:
    todo_tasks : list of tuples. 
    Each tuple construction is (item_id, description). 
    """
    todo_tasks = db.session.query(
        Item.item_id, 
        Item.description
    ).where(Item.list_id==list_id).all()
    return todo_tasks


def retrieve_list_name_by_id(list_id):
    """
    Search for list name from 'To_do_lists' by list_id
    and returns it.
    Attribute:
    list_id : int. List id in 'To_do_lists' db.
    Returns:
    list_name : string. 
    """
    list_name = db.session.query(To_do_list.name).where(
        To_do_list.list_id == list_id).all()
    return list_name[0][0]


@app.route("/items/<list_id>", methods=['GET', 'POST'])
def items(list_id):
    """
    Renders 'items.html' page.
    Performs new task addition,
    task removal, edit, save edits.
    Attributes:
    list_id : int.
    list id by which tasks will be
    filtered from 'Items' db and displayed.
    """
    login = session.get('loged_in')
    user_data = retrieve_user_by_login(login, ['id'])
    list_name = retrieve_list_name_by_id(list_id)
    form_new_task = forms.add_task()
    form_task_holder = forms.single_task()
    
    # add new task 
    if form_new_task.validate_on_submit():
        description = form_new_task.new_task_input.data
        it = Item(
            description=description,
            list_id=list_id)
        db.session.add(it)
        db.session.commit()
        return redirect(url_for("items", list_id=list_id))
    # operations on a task
    elif form_task_holder.validate_on_submit():
        # edit task name
        if form_task_holder.edit.data == True:
            task_list = retrieve_list_task(list_id)
            item_id = form_task_holder.task_id.data
            print(item_id)
            return render_template(
                'items.html',
                list_id=list_id,
                list_name=list_name,
                form_new_task=form_new_task,
                form_task_holder=form_task_holder,
                rows=task_list,
                id=item_id
                )
        # save new task name
        elif form_task_holder.save.data == True:
            item_id = form_task_holder.task_id.data
            task_name = form_task_holder.task_name.data
            db.session.query(Item).filter(Item.item_id == item_id).\
                update({'description': task_name})
            db.session.commit()
        # delete task
        elif form_task_holder.delete.data == True:    
            task_id = form_task_holder.task_id.data
            item = db.session.query(Item).get(task_id)

            db.session.delete(item)
            db.session.commit()

        return redirect(url_for(
            'items',
            list_id=list_id))

    task_list = retrieve_list_task(list_id)        
    print(task_list)

    return render_template(
        "items.html",
        list_id=list_id,
        list_name=list_name,
        form_new_task=form_new_task,
        form_task_holder=form_task_holder,
        rows=task_list,
        id=None
        )
        

if __name__ == '__main__':
    app.run()
