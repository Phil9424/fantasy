from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    Декоратор для проверки, является ли пользователь администратором.
    Если пользователь не администратор, перенаправляет на главную страницу.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('У вас нет доступа к этой странице', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
