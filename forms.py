"""
Contains WTForms
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class signin(FlaskForm):
    login = StringField('Login: ', [Length(min=4, max=30)])
    password = PasswordField('Password:', [Length(min=6, max=30)]) 
    submit = SubmitField('Sign in')


class register(FlaskForm):
    login = StringField('Login: ', [Length(min=4, max=30)])
    password = PasswordField('Password: ', [
        Length(min=6, max=30),
        EqualTo('confirm', 'Passwords must match')
    ])
    confirm = PasswordField('Confirm password: ', [
        Length(min=6, max=30)
    ])
    submit = SubmitField('Register')


class add_list(FlaskForm):
    new_list_input = StringField('new-list-input', validators=[DataRequired()])
    submit = SubmitField('Add list')


class single_list(FlaskForm):
    list_id = StringField(
        validators=[DataRequired()],
        render_kw={
            'hidden': True,
            })
    list_name = StringField(validators=[DataRequired()])
    save = SubmitField()
    delete = SubmitField()
    edit = SubmitField()
    open = SubmitField()


class add_task(FlaskForm):
    new_task_input = StringField('new-task-input', validators=[DataRequired()])
    submit = SubmitField('Add task')


class single_task(FlaskForm):
    task_id = StringField(
        validators=[DataRequired()],
        render_kw={
            'hidden':True,
            'readonly':True
            })
    task_name = StringField(validators=[DataRequired()])
    save = SubmitField()
    delete = SubmitField()
    edit = SubmitField()
    open = SubmitField()

    
