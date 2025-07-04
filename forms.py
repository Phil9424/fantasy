from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Имя пользователя должно быть от 3 до 20 символов')
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message='Введите корректный email адрес')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(),
        Length(min=8, message='Пароль должен содержать не менее 8 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        DataRequired(),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    terms = BooleanField('Я принимаю условия использования', validators=[
        DataRequired(message='Вы должны принять условия использования')
    ])
    newsletter = BooleanField('Получать уведомления')
    submit = SubmitField('Зарегистрироваться')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован. Пожалуйста, используйте другой.')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(),
        Email(message='Введите корректный email адрес')
    ])
    submit = SubmitField('Восстановить пароль')
