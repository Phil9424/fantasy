"""
Утилиты для работы с уведомлениями
"""
from models import db, Notification, User
from datetime import datetime

def create_notification(user_id, type, title, content=None, link=None, icon=None):
    """
    Создает новое уведомление для пользователя
    
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

def create_card_notification(user_id, card_name, rarity, is_prime=False):
    """
    Создает уведомление о получении новой карты
    
    Args:
        user_id (int): ID пользователя
        card_name (str): Название карты
        rarity (int): Редкость карты (1-5)
        is_prime (bool, optional): Является ли карта прайм-версией
    """
    rarity_text = {
        1: "обычную",
        2: "необычную",
        3: "редкую",
        4: "эпическую",
        5: "легендарную"
    }.get(rarity, "")
    
    prime_text = " прайм-версии" if is_prime else ""
    
    title = f"Вы получили {rarity_text} карту \"{card_name}\"{prime_text}"
    
    return create_notification(
        user_id=user_id,
        type="card",
        title=title,
        link="/dashboard#cards"
    )

def create_pack_notification(user_id, pack_name, cards_count):
    """
    Создает уведомление об открытии пака
    
    Args:
        user_id (int): ID пользователя
        pack_name (str): Название пака
        cards_count (int): Количество полученных карт
    """
    title = f"Вы открыли пак \"{pack_name}\" и получили {cards_count} новых карт"
    
    return create_notification(
        user_id=user_id,
        type="pack",
        title=title,
        link="/dashboard#cards"
    )

def create_market_listing_notification(user_id, card_name, price):
    """
    Создает уведомление о выставлении карты на продажу
    
    Args:
        user_id (int): ID пользователя
        card_name (str): Название карты
        price (int): Цена
    """
    title = f"Вы выставили карту \"{card_name}\" на продажу за {price} монет"
    
    return create_notification(
        user_id=user_id,
        type="market",
        title=title,
        link="/market"
    )

def create_market_sale_notification(user_id, card_name, price):
    """
    Создает уведомление о продаже карты
    
    Args:
        user_id (int): ID пользователя
        card_name (str): Название карты
        price (int): Цена
    """
    title = f"Ваша карта \"{card_name}\" продана за {price} монет"
    
    return create_notification(
        user_id=user_id,
        type="sale",
        title=title,
        link="/market"
    )

def create_market_purchase_notification(user_id, card_name, price):
    """
    Создает уведомление о покупке карты
    
    Args:
        user_id (int): ID пользователя
        card_name (str): Название карты
        price (int): Цена
    """
    title = f"Вы купили карту \"{card_name}\" за {price} монет"
    
    return create_notification(
        user_id=user_id,
        type="market",
        title=title,
        link="/dashboard#cards"
    )

def create_transfer_sent_notification(user_id, recipient_username, amount):
    """
    Создает уведомление о переводе монет
    
    Args:
        user_id (int): ID пользователя
        recipient_username (str): Имя получателя
        amount (int): Сумма
    """
    title = f"Вы перевели {amount} монет пользователю {recipient_username}"
    
    return create_notification(
        user_id=user_id,
        type="transfer",
        title=title,
        link="/dashboard"
    )

def create_transfer_received_notification(user_id, sender_username, amount):
    """
    Создает уведомление о получении монет
    
    Args:
        user_id (int): ID пользователя
        sender_username (str): Имя отправителя
        amount (int): Сумма
    """
    title = f"Вы получили {amount} монет от пользователя {sender_username}"
    
    return create_notification(
        user_id=user_id,
        type="coins",
        title=title,
        link="/dashboard"
    )

def create_daily_bonus_notification(user_id, amount):
    """
    Создает уведомление о ежедневном бонусе
    
    Args:
        user_id (int): ID пользователя
        amount (int): Сумма
    """
    title = f"Ежедневный бонус: +{amount} монет"
    content = f"Вы получили ежедневный бонус в размере {amount} монет."
    
    return create_notification(
        user_id=user_id,
        type='coins',
        title=title,
        content=content,
        icon='bi-calendar-check-fill text-success'
    )

def create_tournament_notification(user_id, tournament_id, tournament_name, message):
    """
    Создает уведомление о турнире
    
    Args:
        user_id (int): ID пользователя
        tournament_id (int): ID турнира
        tournament_name (str): Название турнира
        message (str): Сообщение уведомления
    """
    title = f"Турнир: {tournament_name}"
    link = f"/tournaments/{tournament_id}"
    
    return create_notification(
        user_id=user_id,
        type='tournament',
        title=title,
        content=message,
        link=link,
        icon='bi-trophy-fill text-warning'
    )
