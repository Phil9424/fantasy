from app import app, db
from models import User, Notification
from datetime import datetime

with app.app_context():
    # Находим первого пользователя
    user = User.query.first()
    
    if user:
        # Создаем тестовое уведомление
        notification = Notification(
            user_id=user.id,
            type='test',
            title='Тестовое уведомление',
            content='Это тестовое уведомление для проверки системы',
            created_at=datetime.utcnow()
        )
        
        db.session.add(notification)
        db.session.commit()
        
        print(f'Создано тестовое уведомление для пользователя {user.username}')
    else:
        print('Пользователи не найдены. Сначала создайте пользователя.')
