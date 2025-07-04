from flask import Flask, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Card, UserCard, db
import sqlite3
import os
import traceback

def register_routes(app):
    @app.route('/admin/force_delete_card/<int:card_id>')
    @login_required
    def force_delete_card(card_id):
        if not current_user.is_admin:
            flash('У вас нет доступа к админ-панели', 'danger')
            return redirect(url_for('dashboard'))
        
        try:
            # Получаем карту
            card = Card.query.get_or_404(card_id)
            card_name = card.name
            
            # Используем прямые SQL-запросы для обхода ограничений внешних ключей
            import sqlite3
            import os
            
            # Путь к базе данных
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'mafia_fantasy.db')
            
            # Подключаемся к базе данных напрямую
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Отключаем проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Находим все user_card, связанные с этой карточкой
            cursor.execute("SELECT id FROM user_card WHERE card_id = ?", (card_id,))
            user_cards = cursor.fetchall()
            user_card_ids = [uc[0] for uc in user_cards]
            
            # Очищаем ссылки на эти карточки в командах
            for slot in range(1, 5):  # В таблице team есть 4 слота
                if user_card_ids:
                    if len(user_card_ids) == 1:
                        cursor.execute(f"UPDATE team SET card{slot}_id = NULL WHERE card{slot}_id = ?", (user_card_ids[0],))
                    else:
                        placeholders = ','.join(['?'] * len(user_card_ids))
                        cursor.execute(f"UPDATE team SET card{slot}_id = NULL WHERE card{slot}_id IN ({placeholders})", user_card_ids)
            
            # Удаляем записи из user_card
            cursor.execute("DELETE FROM user_card WHERE card_id = ?", (card_id,))
            
            # Удаляем саму карточку
            cursor.execute("DELETE FROM card WHERE id = ?", (card_id,))
            
            # Фиксируем изменения
            conn.commit()
            
            # Включаем обратно проверку внешних ключей
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Закрываем соединение
            conn.close()
            
            flash(f'Карта "{card_name}" успешно удалена', 'success')
            return redirect(url_for('admin_cards'))
        
        except Exception as e:
            # Если есть соединение с базой данных, закрываем его
            try:
                if 'conn' in locals() and conn:
                    conn.rollback()
                    cursor.execute("PRAGMA foreign_keys = ON")
                    conn.close()
            except:
                pass
            
            flash(f'Ошибка при удалении карты: {str(e)}', 'danger')
            return redirect(url_for('admin_cards'))
