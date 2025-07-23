from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms import SubmitField
from wtforms.fields.simple import EmailField, TextAreaField
from wtforms.validators import DataRequired


class Register(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired('Введите корректный Email')])
    password = PasswordField('Пароль', validators=[DataRequired('Пароль обязателен')])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired('Нужно подтвердить пароль')])
    name = StringField('Ваше имя', validators=[DataRequired('Введите Ваше имя')])
    about = TextAreaField('Немного напишите про себя')
    submit = SubmitField('Регистрация')
