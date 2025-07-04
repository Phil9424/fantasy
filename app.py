import os
import shutil
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid
import json
import random
import string
import logging
from logging.handlers import RotatingFileHandler
import tempfile
import io
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import qrcode
import qrcode.image.svg
from sqlalchemy import func, and_, or_, not_, desc
from sqlalchemy.orm import joinedload

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    
    # Database configuration
    if os.environ.get('VERCEL'):
        # On Vercel, use environment variables for database
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
        app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'uploads')
    else:
        # Local development
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mafia_fantasy.db'
        app.config['UPLOAD_FOLDER'] = 'static/uploads'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Configure logging
    if not app.debug:
        handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Import and register blueprints
    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

# Импортируем функции для работы с турнирами
from routes.tournaments import register_tournaments_routes

# Импортируем функции для работы с уведомлениями
from routes.notifications import notifications_bp, register_notifications_routes
from utils.notifications import create_market_listing_notification, create_market_sale_notification, create_market_purchase_notification, create_pack_notification, create_card_notification, create_daily_bonus_notification, create_transfer_sent_notification, create_transfer_received_notification, create_tournament_notification

# Импортируем функции для удаления карточек
from card_deletion import setup_card_deletion_routes
from routes.notifications import register_notifications_routes

# Инициализация приложения
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Конфигурация
import os
import tempfile
from urllib.parse import quote_plus

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
if os.environ.get('DATABASE_URL'):
    # Use PostgreSQL from environment variable (for production)
    db_url = os.environ['DATABASE_URL']
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'uploads')
elif os.environ.get('VERCEL') == '1':  # Running on Vercel without PostgreSQL
    temp_dir = tempfile.gettempdir()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'uploads')
else:  # Local development
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance/mafia_fantasy.db")}'
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Создаем папку для загрузок, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Инициализация расширений
csrf = CSRFProtect(app)
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# CSRF защита уже инициализирована выше

# Add CSRF token to all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# Регистрация отладочных маршрутов
app.register_blueprint(debug.bp, url_prefix='/debug')

# Создаем все таблицы при запуске приложения
with app.app_context():
    if os.environ.get('VERCEL') == '1':
        # На Vercel создаем все таблицы заново при каждом запуске
        db.create_all()
        # Создаем тестовые данные, если нужно
        if not User.query.first():
            create_admin()
    else:
        # В обычном режиме просто создаем таблицы, если их нет
        db.create_all()
        # Создаем администратора, если его нет
        create_admin()

# Загрузчик пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Фильтры для шаблонов
@app.template_filter('rarity_name')
def rarity_name_filter(rarity):
    rarities = {
        1: 'Обычная',
        2: 'Необычная',
        3: 'Редкая',
        4: 'Эпическая',
        5: 'Легендарная'
    }
    return rarities.get(rarity, 'Неизвестная')

@app.template_filter('rarity_color')
def rarity_color_filter(rarity):
    colors = {
        1: 'secondary',
        2: 'info',
        3: 'primary',
        4: 'warning',
        5: 'danger'
    }
    return colors.get(rarity, 'secondary')

# Роуты
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rules')
def rules():
    return render_template('rules.html')

def get_weekly_top_players():
    """Получает топ игроков за неделю с Polemica API и преобразует в нужный формат"""
    try:
        url = 'https://app.polemicagame.com/v1/competitions/scores?federation=1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,zh-TW;q=0.7,zh;q=0.6',
            'Connection': 'keep-alive',
            'Origin': 'https://polemicagame.com',
            'Referer': 'https://polemicagame.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        players_data = response.json()
        
        # Преобразуем данные в нужный формат
        formatted_players = []
        for player in players_data:
            player_id = str(player.get('id', ''))
            # Get avatar path from the API response
            avatar_path = player.get('avatar', '')
            
            if avatar_path and not avatar_path.startswith('http'):
                # Handle different avatar path formats
                if '/' in avatar_path:
                    # If path already contains player ID, use it as is
                    if avatar_path.startswith(f"{player_id}/"):
                        avatar_url = f"https://polemicagame.com/images/avatar/{avatar_path}"
                    else:
                        # Otherwise, construct the full path
                        avatar_url = f"https://polemicagame.com/images/avatar/{player_id}/{avatar_path}"
                else:
                    # Just a filename, add the player ID
                    avatar_url = f"https://polemicagame.com/images/avatar/{player_id}/{avatar_path}"
            else:
                # If no avatar path is provided, use the default avatar
                avatar_url = f"https://polemicagame.com/images/avatar/{player_id}/default.jpg"
                
            # Clean up any double slashes that might occur
            avatar_url = avatar_url.replace('//', '/').replace('https:/', 'https://')
                
            player_data = {
                'position': 0,  # Будет заполнено после сортировки
                'player_name': player.get('username', 'Неизвестный игрок'),
                'tournaments': int(player.get('count', 0)),
                'top3': int(player.get('top3', 0)),
                'top_scores': int(round(float(player.get('topScores', 0)))),
                'total_scores': int(round(float(player.get('totalScores', 0)))),
                'avatar': avatar_url,
                'id': player_id,
                'city': player.get('city', 'Без города')
            }
            print(f"Player {player_data['player_name']} - Avatar URL: {avatar_url}")
            formatted_players.append(player_data)
        
        # Сортируем по убыванию общих очков и берем топ-10
        formatted_players.sort(key=lambda x: x['total_scores'], reverse=True)
        
        # Устанавливаем позиции
        for idx, player in enumerate(formatted_players[:10], 1):
            player['position'] = idx
            
        top_players = formatted_players[:10]
        return top_players
    except Exception as e:
        print(f"Error fetching weekly top players: {e}")
        return []

@app.route('/api/weekly-leaders')
def weekly_leaders_api():
    """API endpoint для получения всего списка игроков"""
    try:
        print("Fetching all weekly leaders from Polemica API...")
        players = get_weekly_top_players()
        
        print(f"Returning {len(players)} players")
        return jsonify({
            'status': 'success',
            'data': players
        })
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'Не удалось получить данные с сервера Polemica',
            'debug': str(e)
        }), 502  # Bad Gateway
    except ValueError as e:
        error_msg = f"JSON decode error: {str(e)}"
        print(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'Ошибка обработки данных от сервера',
            'debug': str(e)
        }), 502
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return jsonify({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера',
            'debug': str(e)
        }), 500

@app.route('/leaderboard')
def leaderboard():
    # Получаем топ игроков по общему количеству очков
    top_players = User.query.order_by(User.points.desc()).limit(10).all()
    
    # Получаем топ игроков за неделю с Polemica API
    weekly_leaders = get_weekly_top_players()
    
    # Получаем список новых игроков (последние зарегистрированные)
    new_players = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Находим позицию текущего пользователя
    current_user_rank = None
    if current_user.is_authenticated:
        # Получаем всех пользователей, отсортированных по очкам
        all_users = User.query.order_by(User.points.desc()).all()
        for i, user in enumerate(all_users, 1):
            if user.id == current_user.id:
                current_user_rank = i
                break
    
    return render_template('leaderboard.html', 
                         players=top_players, 
                         weekly_leaders=weekly_leaders[:5],  # Берем топ-5
                         new_players=new_players,
                         current_user_rank=current_user_rank,
                         now=datetime.utcnow())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Создаем команду для пользователя
        team = Team(user_id=user.id)
        db.session.add(team)
        
        # Выдаем начальные карты
        starter_cards = Card.query.filter(Card.rarity.in_([1, 2])).order_by(db.func.random()).limit(5).all()
        for card in starter_cards:
            user_card = UserCard(user_id=user.id, card_id=card.id)
            db.session.add(user_card)
        
        db.session.commit()
        
        flash('Регистрация прошла успешно! Вам выданы стартовые карты.', 'success')
        return redirect(url_for('login'))
        
    return render_template('auth/register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
        
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if not user or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))
            
        login_user(user, remember=form.remember.data)
        return redirect(url_for('dashboard'))
        
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Здесь будет логика отправки email с инструкциями по восстановлению пароля
            # В данной версии просто показываем сообщение об успехе
            flash('Инструкции по восстановлению пароля отправлены на ваш email', 'success')
        else:
            # Для безопасности не сообщаем, что email не найден
            flash('Инструкции по восстановлению пароля отправлены на ваш email', 'success')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    # Получаем актуальные данные пользователя из базы данных
    user = User.query.get(current_user.id)
    
    # Получаем все карты пользователя с информацией о редкости
    user_cards = UserCard.query.filter_by(user_id=user.id).join(UserCard.card).all()
    
    # Получаем карты в команде с информацией о редкости
    team_cards = []
    if user.team:
        team_cards = [
            UserCard.query.join(UserCard.card).filter(UserCard.id == card_id).first() 
            for card_id in [
                user.team.slot1_card_id,
                user.team.slot2_card_id,
                user.team.slot3_card_id,
                user.team.slot4_card_id
            ] if card_id
        ]
    
    # Получаем активные турниры
    from models import Tournament
    active_tournaments = Tournament.query.filter_by(is_active=True, is_completed=False).all()
    
    # Передаем данные в шаблон
    return render_template('dashboard.html', 
                         user=user, 
                         user_cards=user_cards,
                         team_cards=team_cards,
                         active_tournaments=active_tournaments)

@app.route('/open_pack/<int:pack_id>')
@login_required
def open_pack(pack_id):
    # Получаем пак из базы данных по ID
    pack = Pack.query.get_or_404(pack_id)
    
    # Проверяем, что пак активен
    if not pack.is_active:
        flash('Этот пак недоступен для покупки', 'danger')
        return redirect(url_for('shop'))
    
    # Получаем стоимость пака
    cost = pack.price
    
    try:
        # Получаем актуальные данные пользователя из базы данных
        user = User.query.get(current_user.id)
        
        # Проверяем, есть ли у пользователя достаточно монет
        if current_user.coins < cost:
            flash('У вас недостаточно монет', 'danger')
            return redirect(url_for('shop'))
        
        # Списываем монеты
        current_user.coins -= cost
        
        # Генерируем карты
        new_cards = []
        
        # Количество карт в паке (минимум 1 карта)
        num_cards = max(1, pack.cards_count if hasattr(pack, 'cards_count') else 5)
        
        # Шанс на прайм-карту
        prime_chance = getattr(pack, 'prime_chance', 0.1)
        
        print('\n=== НАЧАЛО ГЕНЕРАЦИИ КАРТ ===')
        print(f'Будет сгенерировано карт: {num_cards}')
        print(f'Диапазон редкостей: {pack.min_rarity}-{pack.max_rarity}')
        print(f'Шанс на прайм: {prime_chance*100}%')
        
        # Выводим список всех доступных карт
        all_cards = Card.query.all()
        print('\nДоступные карты в базе:')
        for c in all_cards:
            print(f'ID: {c.id}, Name: {c.name}, Rarity: {c.rarity}, Prime: {c.is_prime}')
        
        print(f'\n=== Открытие пака "{pack.name}" ===')
        print(f'Запрошено карт: {num_cards}')
        print(f'Минимальная редкость: {pack.min_rarity}, Максимальная редкость: {pack.max_rarity}')
        print(f'Шанс на прайм: {prime_chance*100}%')
        
        # Выводим общее количество карт в базе
        total_cards = Card.query.count()
        print(f'Всего карт в базе: {total_cards}')
        
        # Выводим количество карт по редкостям
        for r in range(1, 6):
            count = Card.query.filter_by(rarity=r).count()
            print(f'Карт с редкостью {r}: {count}')
        
        # Генерируем шансы на карты разной редкости в зависимости от мин. и макс. редкости пака
        rarity_chances = {}
        
        # Диапазон редкости карт в паке
        min_rarity = getattr(pack, 'min_rarity', 1)
        max_rarity = getattr(pack, 'max_rarity', 5)
        print(f'Проверка редкостей: min_rarity={min_rarity}, max_rarity={max_rarity}')
        
        # Распределяем шансы на карты разной редкости
        # Чем выше редкость, тем меньше шанс
        total_rarities = max_rarity - min_rarity + 1
        
        # Если только одна редкость, то шанс 100%
        if total_rarities == 1:
            rarity_chances[min_rarity] = 100
        else:
            # Распределяем шансы в зависимости от редкости
            # Чем выше редкость, тем меньше шанс
            total_weight = 0
            for r in range(min_rarity, max_rarity + 1):
                weight = 100 // (2 ** (r - min_rarity))
                rarity_chances[r] = weight
                total_weight += weight
            
            # Нормализуем шансы, чтобы сумма была 100%
            for r in rarity_chances:
                rarity_chances[r] = int(rarity_chances[r] * 100 / total_weight)                  
        
        # Генерируем карты
        import random
        print(f'\n=== ГЕНЕРАЦИЯ {num_cards} КАРТ ===')
        
        # Получаем все карты, соответствующие редкости пака
        valid_cards = []
        for r in range(pack.min_rarity, pack.max_rarity + 1):
            cards = Card.query.filter_by(rarity=r).all()
            valid_cards.extend(cards)
            
        print(f'Найдено {len(valid_cards)} карт с редкостью {pack.min_rarity}-{pack.max_rarity}')
        
        # Если нет подходящих карт, используем любые карты
        if not valid_cards:
            print('Нет карт с подходящей редкостью, используем все доступные карты')
            valid_cards = Card.query.all()
            
        print(f'Всего доступно карт для выбора: {len(valid_cards)}')
        
        # Генерируем ровно num_cards карт, разрешая дубликаты
        new_cards = []
        for i in range(num_cards):
            print(f'\n--- Генерация карты {i+1}/{num_cards} ---')
            # Выбираем случайную карту из подходящих
            card = random.choice(valid_cards)
            print(f'Выбрана карта: ID={card.id}, Name={card.name}, Rarity={card.rarity}, Prime={card.is_prime}')
            
            # Создаем запись о карте пользователя
            user_card = UserCard(user_id=user.id, card_id=card.id)
            db.session.add(user_card)
            
            # Добавляем карту в список новых карт
            card_data = {
                'id': card.id,
                'name': card.name,
                'image': card.image,
                'rarity': card.rarity,
                'is_prime': card.is_prime,
                'base_points': card.base_points,
                'photo_position': card.photo_position if hasattr(card, 'photo_position') else '50% 50%'
            }
            new_cards.append(card_data)
            print(f'Добавлена карта: {card.name} (Редкость: {card.rarity}, Prime: {card.is_prime})')
            
        print(f'\n=== УСПЕШНО СГЕНЕРИРОВАНО {len(new_cards)} КАРТ ===')
        
        # Сохраняем изменения в базе данных
        db.session.commit()
        
        # Создаем уведомление об открытии пака
        create_pack_notification(
            user_id=user.id,
            pack_name=pack.name,
            cards_count=len(new_cards)
        )
        
        # Создаем уведомления о получении редких карт (редкость 3 и выше)
        for card_data in new_cards:
            if card_data['rarity'] >= 3:  # Только для редких, эпических и легендарных карт
                create_card_notification(
                    user_id=user.id,
                    card_name=card_data['name'],
                    rarity=card_data['rarity'],
                    is_prime=card_data['is_prime']
                )
        
        # Обновляем сессию пользователя
        from flask_login import login_user
        login_user(user)
        
        # Проверяем, сколько карт было сгенерировано
        print(f'\n=== РЕЗУЛЬТАТ ГЕНЕРАЦИИ ===')
        print(f'Успешно сгенерировано карт: {len(new_cards)} из {num_cards}')
        if new_cards:
            print('Полученные карты:')
            for i, card in enumerate(new_cards, 1):
                print(f'  {i}. ID: {card["id"]}, Имя: {card["name"]}, Редкость: {card["rarity"]}, Прайм: {card["is_prime"]}')
        
        # Показываем сообщение об успешной покупке
        flash(f'Вы успешно открыли пак "{pack.name}" и получили {len(new_cards)} карточек!', 'success')
        
        # Отображаем результаты открытия пака
        return render_template('pack_opened.html', cards=new_cards, pack=pack)
    
    except Exception as e:
        # Откатываем транзакцию в случае ошибки
        db.session.rollback()
        error_message = str(e)
        flash(f'Произошла ошибка при открытии пака: {error_message}', 'danger')
        print(f'Ошибка при открытии пака: {error_message}')
        
        # Проверяем, есть ли карты в базе данных
        card_count = Card.query.count()
        print(f'Количество карт в базе данных: {card_count}')
        
        # Проверяем количество карт по редкости
        for rarity in range(1, 6):
            count = Card.query.filter_by(rarity=rarity).count()
            print(f'Карт редкости {rarity}: {count}')
        
        return redirect(url_for('shop'))

@app.route('/daily-bonus', methods=['POST'])
@login_required
def daily_bonus():
    user = current_user
    
    # Проверяем, получал ли пользователь бонус сегодня
    today = datetime.now().date()
    last_bonus_date = user.last_bonus_date
    
    if last_bonus_date and last_bonus_date.date() == today:
        return jsonify({
            'success': False,
            'message': 'Вы уже получили ежедневный бонус сегодня'
        })
    
    # Определяем сумму бонуса (можно сделать случайной или зависящей от дня недели)
    bonus_amount = random.randint(30, 100)
    
    # Начисляем бонус
    user.coins += bonus_amount
    user.last_bonus_date = datetime.now()
    db.session.commit()
    
    # Создаем уведомление о ежедневном бонусе
    create_daily_bonus_notification(
        user_id=user.id,
        amount=bonus_amount
    )
    
    return jsonify({
        'success': True,
        'message': f'Вы получили {bonus_amount} монет в качестве ежедневного бонуса!',
        'amount': bonus_amount,
        'total_coins': user.coins
    })

@app.route('/transfer-coins', methods=['POST'])
@login_required
def transfer_coins():
    data = request.json
    recipient_username = data.get('username')
    amount = data.get('amount')
    
    # Проверка входных данных
    if not recipient_username or not amount:
        return jsonify({
            'success': False,
            'message': 'Необходимо указать имя получателя и сумму'
        })
    
    try:
        amount = int(amount)
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'Сумма перевода должна быть положительной'
            })
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Сумма перевода должна быть числом'
        })
    
    # Проверяем, есть ли у пользователя достаточно монет
    if current_user.coins < amount:
        return jsonify({
            'success': False,
            'message': 'У вас недостаточно монет для перевода'
        })
    
    # Находим получателя
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        return jsonify({
            'success': False,
            'message': 'Пользователь с таким именем не найден'
        })
    
    # Нельзя переводить самому себе
    if recipient.id == current_user.id:
        return jsonify({
            'success': False,
            'message': 'Нельзя переводить монеты самому себе'
        })
    
    try:
        # Создаем транзакцию
        transaction = Transaction(
            from_user_id=current_user.id,
            to_user_id=recipient.id,
            amount=amount,
            transaction_type='transfer'
        )
        db.session.add(transaction)
        
        # Списываем монеты у отправителя
        current_user.coins -= amount
        
        # Начисляем монеты получателю
        recipient.coins += amount
        
        # Сохраняем изменения в базе данных
        db.session.commit()
        
        # Создаем уведомления о переводе
        create_transfer_sent_notification(
            user_id=current_user.id,
            recipient_username=recipient.username,
            amount=amount
        )
        
        create_transfer_received_notification(
            user_id=recipient.id,
            sender_username=current_user.username,
            amount=amount
        )
        
        return jsonify({
            'success': True,
            'message': f'Вы успешно перевели {amount} монет пользователю {recipient.username}',
            'remaining_coins': current_user.coins
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при переводе монет: {str(e)}'
        })

@app.route('/shop')
@login_required
def shop():
    # Получаем активные паки из базы данных
    packs = Pack.query.filter_by(is_active=True).all()
    
    # Получаем ВСЕ карты на рынке (is_for_sale = True) с информацией о продавце
    market_cards = db.session.query(
        UserCard,
        User.username.label('seller_username'),
        User.id.label('seller_id')
    ).join(
        User, UserCard.user_id == User.id
    ).filter(
        UserCard.is_for_sale == True
    ).all()
    
    return render_template('shop.html', 
                         packs=packs, 
                         market_cards=market_cards,
                         current_user_id=current_user.id)

@app.route('/api/user_cards')
@login_required
def get_user_cards():
    user_cards = UserCard.query.filter_by(user_id=current_user.id).all()
    
    cards_data = []
    for user_card in user_cards:
        card = user_card.card
        
        # Проверяем, находится ли карта в команде пользователя
        in_team = False
        team = Team.query.filter_by(user_id=current_user.id).first()
        if team:
            for i in range(1, 6):  # Проверяем все 5 слотов
                slot_attr = f'slot{i}_card_id'
                if getattr(team, slot_attr) == user_card.id:
                    in_team = True
                    break
        
        cards_data.append({
            'id': user_card.id,
            'card_id': card.id,
            'name': card.name,
            'image': card.image,
            'rarity': card.rarity,
            'is_prime': card.is_prime,
            'base_points': card.base_points,
            'in_team': in_team,
            'on_market': user_card.is_for_sale
        })
    
@app.route('/update_team', methods=['GET', 'POST'])
@login_required
def update_team():
    # Handle JSON requests for AJAX calls
    if request.is_json:
        data = request.get_json()
        action = data.get('action')
        card_id = data.get('card_id')
        slot = data.get('slot')
        
        user = User.query.get(current_user.id)
        
        if not user.team:
            team = Team(user_id=user.id)
            db.session.add(team)
            db.session.commit()
        
        if not card_id:
            return jsonify({'success': False, 'error': 'Не указан ID карты'}), 400
        
        user_card = UserCard.query.filter_by(id=card_id, user_id=user.id).first()
        
        if not user_card:
            return jsonify({'success': False, 'error': 'Карта не найдена'}), 404
        
        if action == 'add':
            # Check if card is already in the team
            if user_card.in_team:
                return jsonify({'success': False, 'error': 'Эта карта уже в команде'}), 400
            
            # Find the specified slot or first available
            if slot and slot.isdigit():
                slot = int(slot)
                if 1 <= slot <= 4:
                    slot_attr = f'slot{slot}_card_id'
                    if getattr(user.team, slot_attr) is not None:
                        return jsonify({'success': False, 'error': 'Этот слот уже занят'}), 400
                    setattr(user.team, slot_attr, user_card.id)
                else:
                    return jsonify({'success': False, 'error': 'Некорректный номер слота'}), 400
            else:
                # Find first available slot
                for i in range(1, 5):
                    slot_attr = f'slot{i}_card_id'
                    if getattr(user.team, slot_attr) is None:
                        setattr(user.team, slot_attr, user_card.id)
                        break
                else:
                    return jsonify({'success': False, 'error': 'В команде нет свободных слотов'}), 400
            
            user_card.in_team = True
            db.session.add(user.team)
            db.session.add(user_card)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Карта добавлена в команду!'})
            
        elif action == 'remove':
            # Remove card from team
            card_removed = False
            for i in range(1, 5):
                slot_attr = f'slot{i}_card_id'
                if getattr(user.team, slot_attr) == user_card.id:
                    setattr(user.team, slot_attr, None)
                    card_removed = True
                    break
            
            if not card_removed:
                return jsonify({'success': False, 'error': 'Карта не найдена в команде'}), 404
            
            user_card.in_team = False
            db.session.add(user.team)
            db.session.add(user_card)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Карта удалена из команды!'})
        
        return jsonify({'success': False, 'error': 'Неизвестное действие'}), 400
    
    # Handle regular form submissions (for backward compatibility)
    if request.method == 'POST':
        action = request.form.get('action')
        card_id = request.form.get('card_id', type=int)
        
        if not card_id:
            flash('Не указан ID карты', 'danger')
            return redirect(url_for('update_team'))
        
        user = User.query.get(current_user.id)
        user_card = UserCard.query.filter_by(id=card_id, user_id=user.id).first()
        
        if not user_card:
            flash('Карта не найдена', 'danger')
            return redirect(url_for('update_team'))
        
        if action == 'add':
            # Check if card is already in the team
            if user_card.in_team:
                flash('Эта карта уже в команде', 'warning')
                return redirect(url_for('update_team'))
            
            # Find first available slot
            if not user.team.slot1_card_id:
                user.team.slot1_card_id = user_card.id
            elif not user.team.slot2_card_id:
                user.team.slot2_card_id = user_card.id
            elif not user.team.slot3_card_id:
                user.team.slot3_card_id = user_card.id
            elif not user.team.slot4_card_id:
                user.team.slot4_card_id = user_card.id
            else:
                flash('В команде нет свободных слотов', 'warning')
                return redirect(url_for('update_team'))
            
            user_card.in_team = True
            db.session.add(user.team)
            db.session.add(user_card)
            flash('Карта добавлена в команду!', 'success')
            
        elif action == 'remove':
            # Remove card from team
            card_removed = False
            for i in range(1, 5):
                slot_attr = f'slot{i}_card_id'
                if getattr(user.team, slot_attr) == user_card.id:
                    setattr(user.team, slot_attr, None)
                    card_removed = True
                    break
            
            if not card_removed:
                flash('Карта не найдена в команде', 'danger')
                return redirect(url_for('update_team'))
            
            user_card.in_team = False
            db.session.add(user.team)
            db.session.add(user_card)
            flash('Карта удалена из команды!', 'success')
    
        db.session.commit()
        return redirect(url_for('update_team'))
    
    # GET request - show team management page
    user = User.query.get(current_user.id)
    
    # Get all user cards
    user_cards = UserCard.query.filter(
        UserCard.user_id == user.id,
        UserCard.in_team == False
    ).all()
    
    # Get team cards with their slot information
    team_cards = []
    if user.team:
        # Create a list of (card, slot) tuples for cards in the team
        for slot in range(1, 5):
            card_id = getattr(user.team, f'slot{slot}_card_id')
            if card_id:
                card = UserCard.query.get(card_id)
                if card:
                    card.team_slot = slot  # Add slot information to the card object
                    team_cards.append(card)
    
    return render_template('update_team.html', user=user, user_cards=user_cards, team_cards=team_cards)

@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    return update_user_avatar(current_user.id)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    # Получаем статистику для админ-панели
    total_users = User.query.count()
    total_cards = Card.query.count()
    total_user_cards = UserCard.query.count()
    total_packs = Pack.query.count()
    
    # Получаем последних зарегистрированных пользователей
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    
    # Получаем последние добавленные карты
    recent_cards = Card.query.order_by(Card.id.desc()).limit(8).all()
    
    return render_template('admin/index.html', 
                           total_users=total_users,
                           total_cards=total_cards,
                           total_user_cards=total_user_cards,
                           total_packs=total_packs,
                           recent_users=recent_users,
                           recent_cards=recent_cards)

@app.route('/admin/users')
@login_required
def admin_users():
    # Проверяем, что пользователь администратор
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('dashboard'))
    
    # Получаем всех пользователей
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/cards/add', methods=['GET', 'POST'])
@app.route('/admin/cards/edit/<int:card_id>', methods=['GET', 'POST'])
@login_required
def add_card(card_id=None):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('dashboard'))

    card = Card.query.get_or_404(card_id) if card_id else None

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            rarity = int(request.form.get('rarity'))
            is_prime = 'is_prime' in request.form
            base_points = int(request.form.get('base_points'))
            description = request.form.get('description')
            photo_position = request.form.get('photo_position', '50% 50%')
            country_code = request.form.get('country_code', 'RU')
            image_file = request.files.get('image')

            if card is None:  # Creating a new card
                if not all([name, rarity, image_file]):
                    flash('Имя, редкость и изображение обязательны.', 'danger')
                    return render_template('admin/add_card.html', card=None)
                
                card = Card()
                db.session.add(card)

            card.name = name
            card.rarity = rarity
            card.is_prime = is_prime
            card.base_points = base_points
            card.description = description
            card.photo_position = photo_position
            card.country_code = country_code

            if image_file and image_file.filename:
                # Use the Card model's method to handle the image
                if not card.set_image_from_file(image_file):
                    flash('Ошибка при обработке изображения. Пожалуйста, попробуйте другое изображение.', 'danger')
                    return render_template('admin/add_card.html', card=card)
                
                # Keep the original filename for reference
                filename = secure_filename(image_file.filename)
                card.image = filename

            db.session.commit()
            flash(f'Карта "{card.name}" успешно сохранена!', 'success')
            return redirect(url_for('admin_cards'))

        except ValueError as ve:
            db.session.rollback()
            flash(f'Некорректные данные: {str(ve)}', 'danger')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error saving card: {str(e)}', exc_info=True)
            flash(f'Ошибка при сохранении карты: {str(e)}', 'danger')

    return render_template('admin/add_card.html', card=card)

@app.route('/admin/users/create', methods=['POST'])
@login_required
def admin_create_user():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = 'is_admin' in request.form
        
        # Валидация
        if not all([username, email, password]):
            return jsonify({'success': False, 'message': 'Все поля обязательны для заполнения'}), 400
            
        # Проверяем, существует ли пользователь с таким именем или email
        if User.query.filter((User.username == username) | (User.email == email)).first():
            return jsonify({'success': False, 'message': 'Пользователь с таким именем или email уже существует'}), 400
        
        # Создаем пользователя
        user = User(
            username=username,
            email=email,
            is_admin=is_admin,
            coins=0,
            points=0
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Пользователь успешно создан',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'coins': user.coins,
                'points': user.points
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при создании пользователя: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/update', methods=['POST'])
@login_required
def admin_update_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Обновляем данные пользователя
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = 'is_admin' in request.form
        coins = request.form.get('coins')
        points = request.form.get('points')
        
        # Валидация
        if not all([username, email]):
            return jsonify({'success': False, 'message': 'Все поля обязательны для заполнения'}), 400
            
        # Проверяем, существует ли другой пользователь с таким именем или email
        existing_user = User.query.filter(
            (User.id != user_id) & 
            ((User.username == username) | (User.email == email))
        ).first()
        
        if existing_user:
            return jsonify({'success': False, 'message': 'Пользователь с таким именем или email уже существует'}), 400
        
        # Обновляем данные
        user.username = username
        user.email = email
        user.is_admin = is_admin
        
        # Обновляем монеты и очки, если они указаны
        if coins and coins.isdigit():
            user.coins = int(coins)
        
        if points and points.isdigit():
            user.points = int(points)
        
        # Если указан новый пароль, обновляем его
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Данные пользователя обновлены',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'coins': user.coins,
                'points': user.points
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при обновлении данных пользователя: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Нельзя удалить самого себя
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Вы не можете удалить самого себя'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Пользователь успешно удален'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при удалении пользователя: {str(e)}'}), 500

@app.route('/admin/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Генерируем случайный пароль
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        # Устанавливаем новый пароль
        user.set_password(new_password)
        db.session.commit()
        
        # В реальном приложении здесь должна быть отправка email с новым паролем
        
        return jsonify({
            'success': True, 
            'message': 'Пароль успешно сброшен',
            'new_password': new_password  # В реальном приложении не возвращаем пароль в ответе
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при сбросе пароля: {str(e)}'}), 500

@app.route('/update_user_avatar/<int:user_id>', methods=['POST'])
@login_required
def update_user_avatar(user_id):
    # Проверяем права доступа
    if not current_user.is_admin and current_user.id != user_id:
        if request.is_json:
            return jsonify({'error': 'Доступ запрещен'}), 403
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Проверяем, был ли отправлен файл
    if 'avatar' not in request.files:
        if request.is_json:
            return jsonify({'error': 'Файл не выбран'}), 400
        flash('Файл не выбран', 'danger')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))
    
    file = request.files['avatar']
    
    # Если пользователь не выбрал файл, браузер может отправить пустой файл без имени
    if file.filename == '':
        if request.is_json:
            return jsonify({'error': 'Файл не выбран'}), 400
        flash('Файл не выбран', 'danger')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))
    
    if not file or not allowed_file(file.filename):
        if request.is_json:
            return jsonify({'error': 'Недопустимый формат файла'}), 400
        flash('Недопустимый формат файла. Разрешены только изображения (jpg, png, gif)', 'danger')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))
    
    try:
        # Удаляем старый аватар, если он не стандартный
        if user.avatar and user.avatar != 'default_avatar.png':
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], user.avatar))
            except Exception as e:
                app.logger.error(f'Ошибка при удалении старого аватара: {e}')
        
        # Сохраняем новый аватар
        filename = save_file(file)
        user.avatar = filename
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'avatar_url': url_for('uploaded_file', filename=filename)})
        
        flash('Аватарка успешно обновлена', 'success')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Ошибка при обновлении аватара: {e}')
        if request.is_json:
            return jsonify({'error': 'Ошибка при сохранении файла'}), 500
        
        flash('Ошибка при обновлении аватарки', 'danger')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))
    
    if request.is_json:
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    else:
        flash('Недопустимый формат файла. Разрешены только изображения (jpg, png, gif)', 'danger')
        return redirect(url_for('admin_users' if current_user.is_admin else 'dashboard'))

# Обработка статических файлов
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Функция для проверки разрешенных расширений файлов
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Функция для сохранения загруженного файла с уникальным именем
def save_file(file, folder='uploads'):
    if file and allowed_file(file.filename):
        # Создаем уникальное имя файла
        filename = secure_filename(file.filename)
        # Получаем расширение файла
        ext = filename.rsplit('.', 1)[1].lower()
        # Создаем уникальное имя файла с использованием UUID
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Сохраняем файл в двух местах для совместимости
        # 1. В папке uploads
        uploads_folder = os.path.join(basedir, 'static', 'uploads')
        os.makedirs(uploads_folder, exist_ok=True)
        file_path_uploads = os.path.join(uploads_folder, unique_filename)
        file.save(file_path_uploads)
        
        # 2. Если это карта, то также сохраняем в папке images/cards
        if folder == 'cards':
            cards_folder = os.path.join(basedir, 'static', 'images', 'cards')
            os.makedirs(cards_folder, exist_ok=True)
            # Создаем копию файла
            import shutil
            file_path_cards = os.path.join(cards_folder, unique_filename)
            shutil.copy2(file_path_uploads, file_path_cards)
        
        return unique_filename
    return None

# Функция для создания администратора
def create_admin():
    # Проверяем, существует ли уже администратор
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
    else:
        # Ensure the admin flag is set for the existing admin user
        if not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            print('Admin privileges added to existing user.')
        else:
            print('Admin user already exists.')



def create_admin():
    """Создает администратора"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
    else:
        # Ensure the admin flag is set for the existing admin user
        if not admin.is_admin:
            admin.is_admin = True
            db.session.commit()
            print('Admin privileges added to existing user.')
        else:
            print('Admin user already exists.')

@app.cli.command('create-admin')
def create_admin_command():
    """CLI command to create an admin user"""
    with app.app_context():
        create_admin()

# API для удаления карты
@app.route('/api/cards/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    try:
        user_card = UserCard.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
        
        # Проверяем, не находится ли карта в команде
        team = Team.query.filter_by(user_id=current_user.id).first()
        if team:
            for i in range(1, 6):
                slot_attr = f'slot{i}_card_id'
                if getattr(team, slot_attr, None) == user_card.id:
                    # Удаляем карту из слота команды
                    setattr(team, slot_attr, None)
                    db.session.commit()
                    break
        
        # Удаляем карту
        db.session.delete(user_card)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Карта успешно удалена'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting card {card_id}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

# API для выставления карты на рынок
@app.route('/api/cards/<int:card_id>/market', methods=['POST'])
@login_required
def put_card_on_market(card_id):
    try:
        user_card = UserCard.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
        
        # Проверяем, не находится ли карта в команде
        team = Team.query.filter_by(user_id=current_user.id).first()
        if team:
            for i in range(1, 7):  # Check all 6 slots
                slot_attr = f'slot{i}_card_id'
                if getattr(team, slot_attr, None) == user_card.id:
                    return jsonify({
                        'success': False,
                        'error': 'Нельзя выставить карту на рынок, если она находится в команде'
                    }), 400
        
        # Получаем цену из запроса или используем базовую стоимость карты
        data = request.get_json()
        price = data.get('price', user_card.card.base_points)
        
        # Выставляем карту на рынок с ценой
        user_card.is_for_sale = True
        user_card.price = price
        user_card.listed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Создаем уведомление о выставлении карты на рынок
        create_market_listing_notification(
            user_id=current_user.id,
            card_name=user_card.card.name,
            price=price
        )
        
        return jsonify({
            'success': True,
            'message': 'Карта выставлена на рынок',
            'card_id': user_card.id,
            'price': price
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error in put_card_on_market: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при выставлении карты на рынок: ' + str(e)
        }), 500

# API для продажи карты
@app.route('/api/cards/<int:card_id>/sell', methods=['POST'])
@login_required
def sell_card(card_id):
    try:
        user_card = UserCard.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
        
        # Проверяем, не находится ли карта в команде
        team = Team.query.filter_by(user_id=current_user.id).first()
        if team:
            for i in range(1, 7):  # Check all 6 slots
                slot_attr = f'slot{i}_card_id'
                if getattr(team, slot_attr, None) == user_card.id:
                    return jsonify({
                        'success': False, 
                        'error': 'Нельзя продать карту, если она находится в команде'
                    }), 400
        
        # Рассчитываем стоимость продажи (10% от базовой стоимости)
        sell_price = int(user_card.card.base_points * 0.1)
        
        # Начинаем транзакцию
        try:
            # Начисляем монеты пользователю
            current_user.coins += sell_price
            
            # Удаляем карту
            db.session.delete(user_card)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'new_coins': current_user.coins,
                'message': f'Карта продана за {sell_price} монет'
            }), 200
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Database error during sell_card: {str(e)}')
            return jsonify({
                'success': False, 
                'error': 'Ошибка при сохранении изменений в базе данных'
            }), 500
            
    except Exception as e:
        app.logger.error(f'Error in sell_card: {str(e)}')
        return jsonify({
            'success': False, 
            'error': 'Произошла ошибка при обработке запроса'
        }), 500

# API для снятия карты с рынка
@app.route('/api/cards/<int:card_id>/remove_from_market', methods=['POST'])
@login_required
def remove_from_market(card_id):
    try:
        user_card = UserCard.query.filter_by(id=card_id, user_id=current_user.id).first_or_404()
        
        if not user_card.is_for_sale:
            return jsonify({
                'success': False,
                'error': 'Эта карта не выставлена на продажу'
            }), 400
            
        # Снимаем карту с рынка
        user_card.is_for_sale = False
        user_card.price = 0
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Карта снята с продажи',
            'card_id': user_card.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error removing card from market: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'Произошла ошибка при снятии карты с продажи: ' + str(e)
        }), 500

# API для покупки карты с рынка
@app.route('/api/cards/<int:card_id>/buy', methods=['POST'])
@login_required
def buy_card(card_id):
    try:
        # Получаем данные из запроса
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Отсутствуют данные запроса'
            }), 400
            
        # Находим карту на рынке
        user_card = UserCard.query.filter_by(
            id=card_id,
            is_for_sale=True
        ).first_or_404(description='Карта не найдена или не продается')
        
        # Проверяем, что пользователь не покупает свою же карту
        if user_card.user_id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Вы не можете купить свою же карту'
            }), 400
            
        seller = User.query.get(user_card.user_id)
        if not seller:
            return jsonify({
                'success': False,
                'error': 'Продавец не найден'
            }), 404
            
        # Проверяем цену из запроса
        requested_price = data.get('price', user_card.price)
        if requested_price != user_card.price:
            return jsonify({
                'success': False,
                'error': 'Цена карты изменилась. Пожалуйста, обновите страницу и попробуйте снова.'
            }), 400
            
        # Проверяем, достаточно ли у пользователя монет
        if current_user.coins < requested_price:
            return jsonify({
                'success': False,
                'error': f'Недостаточно монет для покупки. Нужно {requested_price} монет, у вас {current_user.coins} монет.'
            }), 400
            
        # Проверяем, не находится ли карта в команде продавца
        team = Team.query.filter_by(user_id=user_card.user_id).first()
        if team:
            for i in range(1, 7):
                slot_attr = f'slot{i}_card_id'
                if getattr(team, slot_attr, None) == user_card.id:
                    return jsonify({
                        'success': False,
                        'error': 'Карта находится в команде продавца и не может быть продана'
                    }), 400
        
        # Начинаем транзакцию
        db.session.begin_nested()
        
        try:
            # Сохраняем данные о продавце и цене
            seller_id = user_card.user_id
            price = user_card.price
            
            # Передаем карту покупателю
            user_card.user_id = current_user.id
            user_card.is_for_sale = False
            user_card.price = 0
            
            # Переводим деньги продавцу
            seller = User.query.get(seller_id)
            seller.coins += price
            
            # Списываем деньги с покупателя
            current_user.coins -= price
            
            # Создаем запись о транзакции
            transaction = Transaction(
                from_user_id=current_user.id,
                to_user_id=seller_id,
                amount=price,
                card_id=card_id,
                transaction_type='market_purchase'
            )
            db.session.add(transaction)
            
            db.session.commit()
            
            # Создаем уведомление для покупателя
            create_market_purchase_notification(
                user_id=current_user.id,
                card_name=user_card.card.name,
                price=price
            )
            
            # Создаем уведомление для продавца
            create_market_sale_notification(
                user_id=seller_id,
                card_name=user_card.card.name,
                price=price
            )
            
            return jsonify({
                'success': True,
                'message': f'Вы успешно купили карту за {price} монет!',
                'new_balance': current_user.coins
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error processing purchase: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Ошибка при обработке покупки: {str(e)}. Пожалуйста, попробуйте позже.'
            }), 500
            
    except Exception as e:
        app.logger.error(f'Error in buy_card: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# API для получения информации о карте
@app.route('/api/cards/<int:card_id>')
@login_required
def get_card_info(card_id):
    user_card = UserCard.query.filter_by(id=card_id).first_or_404()
    card = user_card.card
    
    return jsonify({
        'id': user_card.id,
        'name': card.name,
        'image': card.image,
        'rarity': card.rarity,
        'rarity_name': rarity_name_filter(card.rarity),
        'is_prime': card.is_prime,
        'base_points': card.base_points,
        'description': card.description
    })


# Маршруты для управления паками в админ-панели
@app.route('/admin/packs')
@login_required
def admin_packs():
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    packs = Pack.query.all()
    return render_template('admin/packs.html', packs=packs)

@app.route('/admin/cards')
@login_required
def admin_cards():
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    cards = Card.query.all()
    return render_template('admin/cards.html', cards=cards)

@app.route('/admin/delete_card/<int:card_id>')
@login_required
def admin_delete_card_direct(card_id):
    print(f"\n\n=== DELETING CARD {card_id} ===\n")
    print(f"Request method: {request.method}")
    print(f"User: {current_user.username} (admin: {current_user.is_admin})")
    
    if not current_user.is_admin:
        print("Access denied: not an admin")
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        print(f"Looking for card with ID: {card_id}")
        card = Card.query.get(card_id)
        
        if card is None:
            print(f"Card with ID {card_id} not found")
            flash(f'Карта с ID {card_id} не найдена', 'danger')
            return redirect(url_for('admin_cards'))
            
        print(f"Found card: {card.name} (ID: {card.id})")
        
        # Проверяем, есть ли у пользователей эта карта
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        print(f"Found {len(user_cards)} user cards with this card")
        
        for user_card in user_cards:
            print(f"Processing user card ID: {user_card.id} for user ID: {user_card.user_id}")
            # Проверяем, не находится ли карта в команде
            team = Team.query.filter_by(user_id=user_card.user_id).first()
            if team:
                print(f"Found team for user ID: {user_card.user_id}")
                for i in range(1, 6):
                    slot_attr = f'slot{i}_card_id'
                    slot_value = getattr(team, slot_attr)
                    print(f"Team slot {i}: {slot_value}")
                    if slot_value == user_card.id:
                        # Удаляем карту из слота команды
                        print(f"Removing card from team slot {i}")
                        setattr(team, slot_attr, None)
                        break
            # Удаляем карту пользователя
            print(f"Deleting user card ID: {user_card.id}")
            db.session.delete(user_card)
        
        # Удаляем саму карту
        print(f"Deleting card ID: {card.id}")
        db.session.delete(card)
        
        print("Committing changes to database")
        db.session.commit()
        
        print("Card successfully deleted")
        flash('Карта успешно удалена', 'success')
        return redirect(url_for('admin_cards'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting card: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка при удалении карты: {str(e)}', 'danger')
        return redirect(url_for('admin_cards'))


@app.route('/api/admin/delete_card/<int:card_id>', methods=['POST'])
@login_required
def api_admin_delete_card(card_id):
    print(f"\n\n=== API DELETING CARD {card_id} ===\n")
    print(f"Request method: {request.method}")
    print(f"User: {current_user.username} (admin: {current_user.is_admin})")
    
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        print(f"Looking for card with ID: {card_id}")
        card = Card.query.get(card_id)
        
        if card is None:
            print(f"Card with ID {card_id} not found")
            return jsonify({'success': False, 'message': f'Карта с ID {card_id} не найдена'}), 404
            
        print(f"Found card: {card.name} (ID: {card.id})")
        
        # Проверяем, есть ли у пользователей эта карта
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        print(f"Found {len(user_cards)} user cards with this card")
        
        for user_card in user_cards:
            print(f"Processing user card ID: {user_card.id} for user ID: {user_card.user_id}")
            # Проверяем, не находится ли карта в команде
            team = Team.query.filter_by(user_id=user_card.user_id).first()
            if team:
                print(f"Found team for user ID: {user_card.user_id}")
                for i in range(1, 6):
                    slot_attr = f'slot{i}_card_id'
                    slot_value = getattr(team, slot_attr)
                    print(f"Team slot {i}: {slot_value}")
                    if slot_value == user_card.id:
                        # Удаляем карту из слота команды
                        print(f"Removing card from team slot {i}")
                        setattr(team, slot_attr, None)
                        break
            # Удаляем карту пользователя
            print(f"Deleting user card ID: {user_card.id}")
            db.session.delete(user_card)
        
        # Удаляем саму карту
        print(f"Deleting card ID: {card.id}")
        db.session.delete(card)
        
        print("Committing changes to database")
        db.session.commit()
        
        print("Card successfully deleted")
        return jsonify({'success': True, 'message': 'Карта успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting card: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Ошибка при удалении карты: {str(e)}'}), 500

@app.route('/admin/packs/add', methods=['POST'])
@login_required
def admin_add_pack():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        # Получаем данные формы
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        cards_count = request.form.get('cards_count')
        min_rarity = request.form.get('min_rarity')
        max_rarity = request.form.get('max_rarity')
        prime_chance = request.form.get('prime_chance')
        is_active = 'is_active' in request.form
        
        # Валидация
        if not all([name, price, cards_count, min_rarity, max_rarity]):
            return jsonify({'success': False, 'message': 'Все обязательные поля должны быть заполнены'}), 400
        
        # Проверяем, что редкость указана корректно
        min_rarity = int(min_rarity)
        max_rarity = int(max_rarity)
        if min_rarity < 1 or min_rarity > 5 or max_rarity < 1 or max_rarity > 5 or min_rarity > max_rarity:
            return jsonify({'success': False, 'message': 'Некорректные значения редкости карт'}), 400
        
        # Проверяем шанс выпадения прайм-карты
        prime_chance = float(prime_chance) if prime_chance else 0.1
        if prime_chance < 0 or prime_chance > 1:
            return jsonify({'success': False, 'message': 'Шанс выпадения прайм-карты должен быть от 0 до 1'}), 400
        
        # Создаем новый пак
        pack = Pack(
            name=name,
            description=description,
            price=int(price),
            cards_count=int(cards_count),
            min_rarity=min_rarity,
            max_rarity=max_rarity,
            prime_chance=prime_chance,
            is_active=is_active
        )
        
        # Обрабатываем изображение пака, если оно загружено
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = save_file(image)
                if filename:
                    pack.image = filename
        
        db.session.add(pack)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Пак успешно добавлен',
            'pack': {
                'id': pack.id,
                'name': pack.name,
                'price': pack.price,
                'cards_count': pack.cards_count,
                'min_rarity': pack.min_rarity,
                'max_rarity': pack.max_rarity,
                'prime_chance': pack.prime_chance,
                'is_active': pack.is_active,
                'image': pack.image
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при добавлении пака: {str(e)}'}), 500

@app.route('/admin/packs/<int:pack_id>/update', methods=['POST'])
@login_required
def admin_update_pack(pack_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        pack = Pack.query.get_or_404(pack_id)
        
        # Получаем данные формы
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        cards_count = request.form.get('cards_count')
        min_rarity = request.form.get('min_rarity')
        max_rarity = request.form.get('max_rarity')
        prime_chance = request.form.get('prime_chance')
        is_active = 'is_active' in request.form
        
        # Валидация
        if not all([name, price, cards_count, min_rarity, max_rarity]):
            return jsonify({'success': False, 'message': 'Все обязательные поля должны быть заполнены'}), 400
        
        # Проверяем, что редкость указана корректно
        min_rarity = int(min_rarity)
        max_rarity = int(max_rarity)
        if min_rarity < 1 or min_rarity > 5 or max_rarity < 1 or max_rarity > 5 or min_rarity > max_rarity:
            return jsonify({'success': False, 'message': 'Некорректные значения редкости карт'}), 400
        
        # Проверяем шанс выпадения прайм-карты
        prime_chance = float(prime_chance) if prime_chance else 0.1
        if prime_chance < 0 or prime_chance > 1:
            return jsonify({'success': False, 'message': 'Шанс выпадения прайм-карты должен быть от 0 до 1'}), 400
        
        # Обновляем данные пака
        pack.name = name
        pack.description = description
        pack.price = int(price)
        pack.cards_count = int(cards_count)
        pack.min_rarity = min_rarity
        pack.max_rarity = max_rarity
        pack.prime_chance = prime_chance
        pack.is_active = is_active
        
        # Обрабатываем изображение пака, если оно загружено
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = save_file(image)
                if filename:
                    pack.image = filename
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Пак успешно обновлен',
            'pack': {
                'id': pack.id,
                'name': pack.name,
                'price': pack.price,
                'cards_count': pack.cards_count,
                'min_rarity': pack.min_rarity,
                'max_rarity': pack.max_rarity,
                'prime_chance': pack.prime_chance,
                'is_active': pack.is_active,
                'image': pack.image
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при обновлении пака: {str(e)}'}), 500

@app.route('/admin/packs/<int:pack_id>/delete', methods=['POST'])
@login_required
def admin_delete_pack(pack_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        pack = Pack.query.get_or_404(pack_id)
        
        db.session.delete(pack)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Пак успешно удален'})
        
    except Exception as e:
        db.session.rollback()
    
    try:
        card = Card.query.get_or_404(card_id)
        
        # Проверяем, есть ли у пользователей эта карта
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        
        for user_card in user_cards:
            # Проверяем, не находится ли карта в команде
            team = Team.query.filter_by(user_id=user_card.user_id).first()
            if team:
                for i in range(1, 6):
                    slot_attr = f'slot{i}_card_id'
                    slot_value = getattr(team, slot_attr)
                    if slot_value == user_card.id:
                        # Удаляем карту из слота команды
                        setattr(team, slot_attr, None)
                        break
            # Удаляем карту пользователя
            db.session.delete(user_card)
        
        # Удаляем саму карту
        db.session.delete(card)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Карта успешно удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Ошибка при удалении карты: {str(e)}'}), 500

@app.route('/admin_delete_card_now/<int:card_id>')
@login_required
def admin_delete_card_now(card_id):
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        print(f"\n\n=== DELETING CARD {card_id} ===\n")
        card = Card.query.get(card_id)
        
        if not card:
            flash(f'Карта с ID {card_id} не найдена', 'danger')
            return redirect(url_for('admin_cards'))
        
        print(f"Found card: {card.name} (ID: {card.id})")
        
        # Проверяем, есть ли у пользователей эта карта
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        print(f"Found {len(user_cards)} user cards with this card")
        
        for user_card in user_cards:
            print(f"Processing user card ID: {user_card.id} for user ID: {user_card.user_id}")
            # Проверяем, не находится ли карта в команде
            team = Team.query.filter_by(user_id=user_card.user_id).first()
            if team:
                print(f"Found team for user ID: {user_card.user_id}")
                for i in range(1, 6):
                    slot_attr = f'slot{i}_card_id'
                    slot_value = getattr(team, slot_attr)
                    print(f"Team slot {i}: {slot_value}")
                    if slot_value == user_card.id:
                        # Удаляем карту из слота команды
                        print(f"Removing card from team slot {i}")
                        setattr(team, slot_attr, None)
                        break
            # Удаляем карту пользователя
            print(f"Deleting user card ID: {user_card.id}")
            db.session.delete(user_card)
        
        # Удаляем саму карту
        print(f"Deleting card ID: {card.id}")
        db.session.delete(card)
        
        print("Committing changes to database")
        db.session.commit()
        
        print("Card successfully deleted")
        flash('Карта успешно удалена', 'success')
        return redirect(url_for('admin_cards'))
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting card: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Ошибка при удалении карты: {str(e)}', 'danger')
        return redirect(url_for('admin_cards'))
@app.route('/admin/confirm_delete_card/<int:card_id>')
@login_required
def confirm_delete_card(card_id):
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    card = Card.query.get_or_404(card_id)
    return render_template('admin/confirm_delete_card.html', card=card)

@app.route('/admin/perform_delete_card/<int:card_id>', methods=['POST'])
@login_required
def perform_delete_card(card_id):
    print("\n\n=== ФУНКЦИЯ perform_delete_card ВЫЗВАНА ===\n")
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        print(f"Начало удаления карты {card_id}")
        
        # Получаем карту
        card = Card.query.get_or_404(card_id)
        print(f"Найдена карта: {card.name} (ID: {card.id})")
        
        # Используем прямые SQL-запросы для обхода ограничений внешних ключей
        from sqlalchemy import text
        
        # Отключаем проверку внешних ключей
        db.session.execute(text("PRAGMA foreign_keys = OFF"))
        
        # Получаем ID всех экземпляров карточки у пользователей
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        user_card_ids = [uc.id for uc in user_cards]
        print(f"Найдено {len(user_cards)} экземпляров карты у пользователей")
        
        # Очищаем ссылки на карточки в командах
        if user_card_ids:
            for slot in range(1, 5):  # В таблице team есть только 4 слота
                if user_card_ids:
                    db.session.execute(
                        text(f"UPDATE team SET card{slot}_id = NULL WHERE card{slot}_id IN :user_card_ids"),
                        {"user_card_ids": tuple(user_card_ids) if len(user_card_ids) > 1 else (user_card_ids[0],)}
                    )
                    print(f"Очищены ссылки в слоте {slot} команд")
        
        # Удаляем записи из user_card
        if user_card_ids:
            db.session.execute(
                text("DELETE FROM user_card WHERE card_id = :card_id"),
                {"card_id": card.id}
            )
            print(f"Удалены записи из user_card")
        
        # Удаляем саму карту
        db.session.execute(
            text("DELETE FROM card WHERE id = :card_id"),
            {"card_id": card.id}
        )
        print(f"Удалена карта из таблицы card")
        
        # Фиксируем изменения
        db.session.commit()
        
        # Включаем обратно проверку внешних ключей
        db.session.execute(text("PRAGMA foreign_keys = ON"))
        
        print("=== КАРТА УСПЕШНО УДАЛЕНА ===\n")
        flash('Карта успешно удалена', 'success')
        return redirect(url_for('admin_cards'))
    
    except Exception as e:
        db.session.rollback()
        # Включаем обратно проверку внешних ключей
        db.session.execute(text("PRAGMA foreign_keys = ON"))
        
        print(f"\n=== ОШИБКА ПРИ УДАЛЕНИИ КАРТЫ ===")
        print(f"Ошибка: {str(e)}")
        print(f"Тип ошибки: {type(e).__name__}")
        print("Полный стек ошибки:")
        import traceback
        traceback.print_exc()
        print("=== КОНЕЦ ОТЧЕТА ОБ ОШИБКЕ ===\n")
        flash(f'Ошибка при удалении карты: {str(e)}', 'danger')
        return redirect(url_for('admin_cards'))

# Новый маршрут для удаления карточек с прямым доступом (для отладки)
@app.route('/admin/delete_card_direct/<int:card_id>')
@login_required
def delete_card_direct(card_id):
    print("\n\n=== ФУНКЦИЯ delete_card_direct ВЫЗВАНА ===\n")
    if not current_user.is_admin:
        flash('У вас нет доступа к админ-панели', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        print(f"Начало прямого удаления карты {card_id}")
        
        # Получаем карту
        card = Card.query.get_or_404(card_id)
        print(f"Найдена карта: {card.name} (ID: {card.id})")
        
        # Проверяем, есть ли у пользователей эта карта
        user_cards = UserCard.query.filter_by(card_id=card.id).all()
        print(f"Найдено {len(user_cards)} экземпляров карты у пользователей")
        
        # Удаляем карты пользователей
        for user_card in user_cards:
            # Проверяем, не находится ли карта в команде
            team = Team.query.filter_by(user_id=user_card.user_id).first()
            if team:
                for i in range(1, 6):
                    slot_attr = f'slot{i}_card_id'
                    if getattr(team, slot_attr) == user_card.id:
                        setattr(team, slot_attr, None)
                        break
            # Удаляем карту пользователя
            db.session.delete(user_card)
        
        # Удаляем саму карту
        db.session.delete(card)
        db.session.commit()
        
        print("Карта успешно удалена")
        flash('Карта успешно удалена', 'success')
        return redirect(url_for('admin_cards'))
    
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении карты: {str(e)}")
        traceback.print_exc()
        flash(f'Ошибка при удалении карты: {str(e)}', 'danger')
        return redirect(url_for('admin_cards'))


# Маршрут для страницы удаления карточек
@app.route('/admin/delete-cards')
@login_required
def admin_delete_cards():
    if current_user.username != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('admin/delete_cards.html')

# Маршрут для страницы тестирования уведомлений
@app.route('/notifications/test')
@login_required
def notification_test():
    return render_template('notification_test.html')

# Маршрут для страницы всех уведомлений
@app.route('/notifications/all')
@login_required
def notifications_all():
    return render_template('notifications_all.html')





# API для получения списка всех карточек
@app.route('/api/admin/cards')
@login_required
def api_admin_cards():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    cards = Card.query.all()
    cards_list = [{
        "id": card.id,
        "name": card.name,
        "rarity": card.rarity
    } for card in cards]
    
    return jsonify(cards_list)

# Регистрируем маршруты для удаления карточек
setup_card_deletion_routes(app, Card)

# Импортируем и регистрируем блюпринт для резервного копирования
from admin_backup import backup_bp
app.register_blueprint(backup_bp)

# Регистрируем маршруты для уведомлений
register_notifications_routes(app)

# Регистрируем маршруты для турниров
register_tournaments_routes(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
