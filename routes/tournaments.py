from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Tournament, TournamentParticipant, TournamentResult, Card, UserCard, Notification
from datetime import datetime
from utils.notifications import create_tournament_notification
from utils.decorators import admin_required
import random

tournaments_bp = Blueprint('tournaments', __name__)

# Регистрация маршрутов для турниров
def register_tournaments_routes(app):
    app.register_blueprint(tournaments_bp, url_prefix='/tournaments')

# Страница со списком всех турниров
@tournaments_bp.route('/')
@login_required
def tournaments_list():
    active_tournaments = Tournament.query.filter_by(is_active=True, is_completed=False).all()
    completed_tournaments = Tournament.query.filter_by(is_completed=True).all()
    
    return render_template('tournaments/list.html', 
                           active_tournaments=active_tournaments,
                           completed_tournaments=completed_tournaments)

# Страница с деталями турнира
@tournaments_bp.route('/<int:tournament_id>')
@login_required
def tournament_details(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = TournamentParticipant.query.filter_by(tournament_id=tournament_id).all()
    
    # Проверяем, зарегистрирован ли пользователь на турнир
    user_registration = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id, 
        user_id=current_user.id
    ).first()
    
    user_registered = user_registration is not None
    
    # Проверяем, есть ли у пользователя команда
    has_team = current_user.team is not None
    
    # Получаем карты пользователя для отображения в других разделах
    user_cards = UserCard.query.join(Card).filter(
        UserCard.user_id == current_user.id,
        UserCard.is_for_sale == False
    ).all()
    
    # Получаем результаты турнира, если он завершен
    results = None
    if tournament.is_completed:
        results = TournamentResult.query.filter_by(tournament_id=tournament_id).order_by(TournamentResult.place).all()
    
    return render_template('tournaments/details.html',
                         tournament=tournament,
                         participants=participants,
                         user_registered=user_registered,
                         user_registration=user_registration,
                         user_cards=user_cards,
                         has_team=has_team,
                         results=results)

# Регистрация на турнир
@tournaments_bp.route('/<int:tournament_id>/register', methods=['POST'])
@login_required
def register_for_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    # Проверяем, открыта ли регистрация
    if not tournament.registration_open:
        flash('Регистрация на турнир закрыта', 'danger')
        return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))
    
    # Проверяем, не зарегистрирован ли уже пользователь
    existing_registration = TournamentParticipant.query.filter_by(
        tournament_id=tournament_id, 
        user_id=current_user.id
    ).first()
    
    if existing_registration:
        flash('Вы уже зарегистрированы на этот турнир', 'warning')
        return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))
    
    # Проверяем, что у пользователя есть команда
    if not current_user.team:
        flash('У вас не сформирована команда. Пожалуйста, создайте команду в профиле.', 'danger')
        return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))
    
    # Получаем карты из команды пользователя
    team = current_user.team
    card1 = team.slot1_card
    card2 = team.slot2_card
    card3 = team.slot3_card
    card4 = team.slot4_card
    
    # Проверяем, что все слоты команды заполнены
    if not all([card1, card2, card3, card4]):
        flash('В вашей команде не все слоты заполнены. Пожалуйста, заполните все слоты в профиле.', 'danger')
        return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))
    
    # Получаем ID карт из команды
    card1_id = card1.id
    card2_id = card2.id
    card3_id = card3.id
    card4_id = card4.id
    
    # Проверяем, что карты принадлежат пользователю
    user_cards = UserCard.query.filter(
        UserCard.id.in_([card1_id, card2_id, card3_id, card4_id]),
        UserCard.user_id == current_user.id
    ).all()
    
    if len(user_cards) != 4:
        flash('Ошибка: не все карты из вашей команды найдены', 'danger')
        return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))
    
    # Создаем запись об участии
    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=current_user.id,
        card1_id=card1_id,
        card2_id=card2_id,
        card3_id=card3_id,
        card4_id=card4_id
    )
    
    db.session.add(participant)
    db.session.commit()
    
    # Создаем уведомление о регистрации
    create_tournament_notification(
        user_id=current_user.id,
        tournament_id=tournament_id,
        tournament_name=tournament.name,
        message=f"Вы успешно зарегистрировались на турнир {tournament.name}"
    )
    
    flash('Вы успешно зарегистрировались на турнир', 'success')
    return redirect(url_for('tournaments.tournament_details', tournament_id=tournament_id))

# Маршруты для администратора

# Страница создания турнира
@tournaments_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
def admin_create_tournament():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('tournaments.tournaments_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_date_str = request.form.get('start_date')
        stars = int(request.form.get('stars', 1))
        is_test = 'is_test' in request.form
        
        # Проверка данных
        if not name or not start_date_str:
            flash('Заполните все обязательные поля', 'danger')
            return render_template('tournaments/admin_create.html')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Неверный формат даты', 'danger')
            return render_template('tournaments/admin_create.html')
        
        # Создаем турнир
        # Добавляем 7 дней к дате начала для получения даты окончания
        from datetime import timedelta
        end_date = start_date + timedelta(days=7)
        
        tournament = Tournament(
            name=name,
            start_time=start_date,
            end_time=end_date,
            start_date=start_date,
            stars=stars,
            is_test=is_test,
            created_by=current_user.id
        )
        
        db.session.add(tournament)
        db.session.commit()
        
        flash(f'Турнир "{name}" успешно создан', 'success')
        return redirect(url_for('tournaments.admin_tournaments'))
    
    return render_template('tournaments/admin_create.html')

# Страница со списком турниров для администратора
@tournaments_bp.route('/admin')
@login_required
def admin_tournaments():
    if not current_user.is_admin:
        flash('У вас нет доступа к этой странице', 'danger')
        return redirect(url_for('index'))
    
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).all()
    return render_template('tournaments/admin_list.html', tournaments=tournaments)

# Страница с деталями турнира для администратора
@tournaments_bp.route('/admin/<int:tournament_id>')
@login_required
def admin_tournament_details(tournament_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('tournaments.tournaments_list'))
    
    tournament = Tournament.query.get_or_404(tournament_id)
    participants = TournamentParticipant.query.filter_by(tournament_id=tournament_id).all()
    
    # Получаем результаты турнира, если он завершен
    results = None
    if tournament.is_completed:
        results = TournamentResult.query.filter_by(tournament_id=tournament_id).order_by(TournamentResult.place).all()
    
    return render_template('tournaments/admin_details.html', 
                           tournament=tournament,
                           participants=participants,
                           results=results)

# Закрыть регистрацию на турнир
@tournaments_bp.route('/admin/<int:tournament_id>/close-registration', methods=['POST'])
@login_required
def admin_close_registration(tournament_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('tournaments.tournaments_list'))
    
    tournament = Tournament.query.get_or_404(tournament_id)
    tournament.registration_open = False
    db.session.commit()
    
    flash('Регистрация на турнир закрыта', 'success')
    return redirect(url_for('tournaments.admin_tournament_details', tournament_id=tournament_id))

# Создать тестовый турнир с 10 игроками
@tournaments_bp.route('/admin/create-test', methods=['GET', 'POST'])
@login_required
def admin_create_test_tournament():
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('tournaments.tournaments_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        start_date_str = request.form.get('start_date')
        stars = int(request.form.get('stars', 1))
        
        # Проверка данных
        if not name or not start_date_str:
            flash('Заполните все обязательные поля', 'danger')
            return render_template('tournaments/admin_create_test.html')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Неверный формат даты', 'danger')
            return render_template('tournaments/admin_create_test.html')
        
        # Создаем тестовый турнир
        # Добавляем 7 дней к дате начала для получения даты окончания
        from datetime import timedelta
        end_date = start_date + timedelta(days=7)
        
        tournament = Tournament(
            name=name,
            start_time=start_date,
            end_time=end_date,
            start_date=start_date,
            stars=stars,
            is_test=True,
            created_by=current_user.id
        )
        
        db.session.add(tournament)
        db.session.commit()
        
        # Получаем все карты для выбора участников турнира
        cards = Card.query.all()
        if len(cards) < 10:
            flash('Недостаточно карт для создания тестового турнира', 'danger')
            return redirect(url_for('tournaments.admin_tournaments'))
        
        # Создаем турнир с 10 участниками (именами игроков из карточек)
        # Выбираем 10 разных карт из базы данных
        tournament_cards = random.sample(cards, 10)
        
        # Задаем результаты для каждого участника (карты)
        test_scores = [6.4, 5.5, 5.4, 5.2, 4.9, 4.5, 4.15, 3.0, 2.9, 0.55]
        
        # Удаляем все существующие результаты для этого турнира
        TournamentResult.query.filter_by(tournament_id=tournament.id).delete()
        
        # Создаем результаты для каждого участника (карты)
        for i, (card, score) in enumerate(zip(tournament_cards, test_scores)):
            result = TournamentResult(
                tournament_id=tournament.id,
                card_id=card.id,  # Карта - это участник турнира
                score=score,      # Баллы участника
                place=i+1         # Место участника
            )
            db.session.add(result)
        
        # Сохраняем результаты в базу данных
        db.session.commit()
        
        # Удаляем все существующие ставки на этот турнир
        TournamentParticipant.query.filter_by(tournament_id=tournament.id).delete()
        
        # В реальном приложении пользователи сами регистрируют свои команды (ставки)
        # Для тестового турнира мы не создаем автоматические ставки
        # Пользователи смогут сами зарегистрироваться на турнир и выбрать карты
        
        # Сообщаем о создании тестового турнира
        flash(f'Тестовый турнир "{name}" успешно создан с 10 участниками (картами). Пользователи могут регистрировать свои команды.', 'success')
        
        db.session.commit()
        
        flash(f'Тестовый турнир "{name}" успешно создан с 10 игроками', 'success')
        return redirect(url_for('tournaments.admin_tournament_details', tournament_id=tournament.id))
    
    return render_template('tournaments/admin_create_test.html')

# Удалить турнир
@tournaments_bp.route('/admin/<int:tournament_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    
    # Удаляем все связанные записи
    # Сначала удаляем результаты турнира
    TournamentResult.query.filter_by(tournament_id=tournament_id).delete()
    
    # Затем удаляем участников турнира
    TournamentParticipant.query.filter_by(tournament_id=tournament_id).delete()
    
    # Удаляем уведомления, связанные с турниром
    # В модели Notification нет поля tournament_id, поэтому мы не можем удалить их напрямую
    # Вместо прямого удаления, найдем и удалим уведомления по одному
    tournament_notifications = Notification.query.filter(
        Notification.type == 'tournament',
        Notification.content.like(f'%{tournament.name}%')
    ).all()
    
    for notification in tournament_notifications:
        db.session.delete(notification)
    
    # Удаляем сам турнир
    db.session.delete(tournament)
    db.session.commit()
    
    flash(f'Турнир "{tournament.name}" был успешно удален', 'success')
    return redirect(url_for('tournaments.admin_tournaments'))

# Завершить турнир и подвести итоги
@tournaments_bp.route('/admin/<int:tournament_id>/complete', methods=['POST'])
@login_required
def admin_complete_tournament(tournament_id):
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('tournaments.tournaments_list'))
    
    tournament = Tournament.query.get_or_404(tournament_id)
    
    # Проверяем, есть ли уже результаты
    existing_results = TournamentResult.query.filter_by(tournament_id=tournament_id).first()
    
    if not existing_results and not tournament.is_test:
        # Для обычных турниров нужно вручную добавить результаты
        flash('Сначала добавьте результаты турнира', 'warning')
        return redirect(url_for('tournaments.admin_tournament_details', tournament_id=tournament_id))
    
    # Закрываем турнир
    tournament.registration_open = False
    tournament.is_completed = True
    db.session.commit()
    
    # Начисляем очки участникам
    participants = TournamentParticipant.query.filter_by(tournament_id=tournament_id).all()
    results = TournamentResult.query.filter_by(tournament_id=tournament_id).all()
    
    # Создаем словарь результатов для быстрого поиска
    results_dict = {result.card_id: result for result in results}
    
    for participant in participants:
        total_points = 0
        
        # Проверяем каждую карту участника
        for card_field in ['card1', 'card2', 'card3', 'card4']:
            card = getattr(participant, card_field)
            if card and card.card_id in results_dict:
                result = results_dict[card.card_id]
                
                # Начисляем очки в зависимости от места
                if result.place == 1:
                    total_points += 100
                elif result.place == 2:
                    total_points += 50
                elif result.place == 3:
                    total_points += 30
                elif result.place == 4:
                    total_points += 20
        
        # Начисляем очки пользователю
        participant.user.points += total_points
        
        # Начисляем монеты в зависимости от набранных очков
        coins_reward = 0
        if total_points >= 100:  # 1 место
            coins_reward = 500
        elif total_points >= 50:  # 2 место
            coins_reward = 300
        elif total_points >= 30:  # 3 место
            coins_reward = 200
        elif total_points >= 20:  # 4 место
            coins_reward = 100
        elif total_points > 0:  # Участие
            coins_reward = 50
            
        # Добавляем монеты пользователю
        if coins_reward > 0:
            participant.user.coins += coins_reward
        
        # Создаем уведомление о результатах
        if total_points > 0 or coins_reward > 0:
            message = f"Вы получили {total_points} очков"
            if coins_reward > 0:
                message += f" и {coins_reward} монет"
            message += f" за участие в турнире {tournament.name}"
            
            create_tournament_notification(
                user_id=participant.user_id,
                tournament_id=tournament_id,
                tournament_name=tournament.name,
                message=message
            )
    
    db.session.commit()
    
    flash('Турнир завершен и очки начислены участникам', 'success')
    return redirect(url_for('tournaments.admin_tournament_details', tournament_id=tournament_id))
