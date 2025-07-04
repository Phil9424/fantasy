from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
    transaction_type = db.Column(db.String(50), nullable=False)  # 'market_purchase', 'pack_purchase', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='outgoing_transactions')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='incoming_transactions')
    card = db.relationship('Card', backref='transactions')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    coins = db.Column(db.Integer, default=1000)
    avatar = db.Column(db.String(120), default='default_avatar.png')
    cards = db.relationship('UserCard', backref='owner', lazy=True)
    team = db.relationship('Team', backref='user', uselist=False, lazy=True)
    points = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    last_bonus_date = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    rarity = db.Column(db.Integer, nullable=False)  # 1-5, где 5 - легендарная
    is_prime = db.Column(db.Boolean, default=False)
    base_points = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    photo_position = db.Column(db.String(50), nullable=True, default='50% 50%')
    country_code = db.Column(db.String(2), nullable=True, default='RU')  # Two-letter country code (ISO 3166-1 alpha-2)
    user_cards = db.relationship('UserCard', backref='card', lazy=True)

class UserCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    in_team = db.Column(db.Boolean, default=False)
    is_for_sale = db.Column(db.Boolean, default=False)
    price = db.Column(db.Integer, default=0)
    listed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def on_market(self):
        return self.is_for_sale
        
    @property
    def seller_username(self):
        return self.owner.username if self.owner else 'Unknown'
        
    @property
    def seller_id(self):
        return self.user_id

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    slot1_card_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    slot2_card_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    slot3_card_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    slot4_card_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    tournament_points = db.Column(db.Integer, default=0)
    
    # Relationships for easier access to team cards
    slot1_card = db.relationship('UserCard', foreign_keys=[slot1_card_id], post_update=True)
    slot2_card = db.relationship('UserCard', foreign_keys=[slot2_card_id], post_update=True)
    slot3_card = db.relationship('UserCard', foreign_keys=[slot3_card_id], post_update=True)
    slot4_card = db.relationship('UserCard', foreign_keys=[slot4_card_id], post_update=True)
    
    def get_slot_card(self, slot_number):
        """Helper method to get card in a specific slot"""
        if 1 <= slot_number <= 4:
            return getattr(self, f'slot{slot_number}_card')
        return None
    
    def set_slot_card(self, slot_number, user_card):
        """Helper method to set card in a specific slot"""
        if 1 <= slot_number <= 4:
            setattr(self, f'slot{slot_number}_card_id', user_card.id if user_card else None)
            return True
        return False

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)  # Дата и время начала турнира
    end_time = db.Column(db.DateTime, nullable=False)  # Дата и время окончания турнира
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Дата начала турнира
    stars = db.Column(db.Integer, default=1)  # Количество звезд турнира (1-5)
    is_test = db.Column(db.Boolean, default=False)  # Является ли турнир тестовым
    registration_open = db.Column(db.Boolean, default=True)  # Открыта ли регистрация
    is_active = db.Column(db.Boolean, default=True)  # Активен ли турнир
    is_completed = db.Column(db.Boolean, default=False)  # Завершен ли турнир
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Кто создал турнир
    
    # Отношения
    participants = db.relationship('TournamentParticipant', backref='tournament', lazy=True)
    results = db.relationship('TournamentResult', backref='tournament', lazy=True)
    creator = db.relationship('User', backref='created_tournaments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'stars': self.stars,
            'is_test': self.is_test,
            'registration_open': self.registration_open,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'participants_count': len(self.participants)
        }

class TournamentParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Карты, выбранные для участия в турнире
    card1_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    card2_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    card3_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    card4_id = db.Column(db.Integer, db.ForeignKey('user_card.id'), nullable=True)
    
    # Отношения
    user = db.relationship('User', backref='tournament_participations')
    card1 = db.relationship('UserCard', foreign_keys=[card1_id])
    card2 = db.relationship('UserCard', foreign_keys=[card2_id])
    card3 = db.relationship('UserCard', foreign_keys=[card3_id])
    card4 = db.relationship('UserCard', foreign_keys=[card4_id])
    
    # Уникальное ограничение: пользователь может участвовать в турнире только один раз
    __table_args__ = (db.UniqueConstraint('tournament_id', 'user_id', name='unique_tournament_participant'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'user_id': self.user_id,
            'username': self.user.username,
            'registered_at': self.registered_at.strftime('%Y-%m-%d %H:%M'),
            'cards': [
                self.card1.card.name if self.card1 else None,
                self.card2.card.name if self.card2 else None,
                self.card3.card.name if self.card3 else None,
                self.card4.card.name if self.card4 else None
            ]
        }

class TournamentResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Результат карты в турнире
    place = db.Column(db.Integer, nullable=False)  # Место карты в турнире
    
    # Отношения
    card = db.relationship('Card', backref='tournament_results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'card_id': self.card_id,
            'card_name': self.card.name,
            'score': self.score,
            'place': self.place
        }

class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(120))
    cards_count = db.Column(db.Integer, default=1)  # Количество карт в паке
    min_rarity = db.Column(db.Integer, default=1)  # Минимальная редкость карт в паке
    max_rarity = db.Column(db.Integer, default=5)  # Максимальная редкость карт в паке
    prime_chance = db.Column(db.Float, default=0.1)  # Шанс выпадения прайм-карты (от 0 до 1)
    is_active = db.Column(db.Boolean, default=True)  # Активен ли пак в магазине

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'card', 'coins', 'market', 'pack', 'transfer', 'sale'
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)  # Дополнительное содержимое, если нужно
    link = db.Column(db.String(255), nullable=True)  # Ссылка для перехода
    icon = db.Column(db.String(100), nullable=True)  # Класс иконки
    is_read = db.Column(db.Boolean, default=False)  # Прочитано ли уведомление
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношение с пользователем
    user = db.relationship('User', backref=db.backref('notifications', lazy=True, order_by='desc(Notification.created_at)'))
    
    def to_dict(self):
        """Преобразует уведомление в словарь для API"""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'link': self.link,
            'icon': self.icon,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'time_display': self.created_at.strftime('%H:%M')
        }
