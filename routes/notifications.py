from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from models import db, Notification, User
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Получение списка непрочитанных уведомлений для текущего пользователя"""
    # Получаем только непрочитанные уведомления
    notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).order_by(
        Notification.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'notifications': [notification.to_dict() for notification in notifications],
        'count': len(notifications)
    })

@notifications_bp.route('/unread', methods=['GET'])
@login_required
def get_unread_notifications():
    """Получение списка непрочитанных уведомлений для текущего пользователя"""
    # Получаем только непрочитанные уведомления
    notifications = Notification.query.filter_by(
        user_id=current_user.id, 
        is_read=False
    ).order_by(
        Notification.created_at.desc()
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'notifications': [notification.to_dict() for notification in notifications],
        'count': len(notifications)
    })

@notifications_bp.route('/all', methods=['GET'])
@login_required
def get_all_notifications():
    """Получение всех уведомлений для текущего пользователя (включая прочитанные)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Получаем все уведомления с пагинацией
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'notifications': [notification.to_dict() for notification in notifications.items],
        'total': notifications.total,
        'pages': notifications.pages,
        'current_page': notifications.page
    })

@notifications_bp.route('/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Отметка уведомления как прочитанного"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Уведомление отмечено как прочитанное'
    })

@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """Отметка всех уведомлений пользователя как прочитанных"""
    Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).update({'is_read': True})
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Все уведомления отмечены как прочитанные'
    })

@notifications_bp.route('/create', methods=['POST'])
@login_required
def create_notification():
    """Создание нового уведомления (для тестирования)"""
    data = request.json
    
    # Проверка наличия обязательных полей
    if not all(key in data for key in ['type', 'title']):
        return jsonify({
            'success': False,
            'message': 'Отсутствуют обязательные поля'
        }), 400
    
    # Создаем новое уведомление
    notification = Notification(
        user_id=current_user.id,
        type=data['type'],
        title=data['title'],
        content=data.get('content'),
        link=data.get('link'),
        icon=data.get('icon'),
        created_at=datetime.utcnow()
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Уведомление создано',
        'notification': notification.to_dict()
    })

def add_notification(user_id, type, title, content=None, link=None, icon=None):
    """
    Служебная функция для добавления уведомления из любой части приложения
    
    Args:
        user_id (int): ID пользователя
        type (str): Тип уведомления ('card', 'coins', 'market', 'pack', 'transfer', 'sale')
        title (str): Заголовок уведомления
        content (str, optional): Дополнительное содержимое
        link (str, optional): Ссылка для перехода
        icon (str, optional): Класс иконки
    
    Returns:
        Notification: Созданное уведомление
    """
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        link=link,
        icon=icon,
        created_at=datetime.utcnow()
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return notification

def register_notifications_routes(app):
    """Регистрация маршрутов для уведомлений"""
    app.register_blueprint(notifications_bp)
