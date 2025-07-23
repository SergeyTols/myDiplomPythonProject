from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired('Введите заголовок')])
    content = TextAreaField('Содержание')
    is_private = BooleanField('Личное')
    submit = SubmitField('Применить')
