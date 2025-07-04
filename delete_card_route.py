#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Отдельный Flask-сервер для удаления карточек.
Запускается на порту 5001 и предоставляет простой интерфейс для удаления карточек.
"""

from flask import Flask, redirect, url_for, flash, render_template
import sqlite3
import os
import sys

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'mafia_fantasy.db')

@app.route('/')
def index():
    """Главная страница с информацией о скрипте."""
    return """
    <h1>Утилита для удаления карточек</h1>
    <p>Используйте URL вида <code>/delete/ID</code>, где ID - идентификатор карточки, которую нужно удалить.</p>
    """

@app.route('/delete/<int:card_id>')
def delete_card(card_id):
    """Удаляет карточку и все связанные записи из базы данных."""
    try:
        print(f"Начало удаления карточки {card_id}")
        
        # Проверяем, существует ли база данных
        if not os.path.exists(DB_PATH):
            return f"Ошибка: База данных не найдена по пути {DB_PATH}"
        
        # Подключаемся к базе данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли карточка
        cursor.execute("SELECT id, name FROM card WHERE id = ?", (card_id,))
        card = cursor.fetchone()
        
        if not card:
            return f"Ошибка: Карточка с ID {card_id} не найдена"
        
        card_name = card[1]
        
        # Отключаем проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Находим все user_card, связанные с этой карточкой
        cursor.execute("SELECT id FROM user_card WHERE card_id = ?", (card_id,))
        user_cards = cursor.fetchall()
        user_card_ids = [uc[0] for uc in user_cards]
        
        # Очищаем ссылки на эти карточки в командах
        if user_card_ids:
            for slot in range(1, 5):  # В таблице team есть только 4 слота
                if len(user_card_ids) == 1:
                    cursor.execute(f"UPDATE team SET card{slot}_id = NULL WHERE card{slot}_id = ?", (user_card_ids[0],))
                else:
                    placeholders = ','.join(['?'] * len(user_card_ids))
                    cursor.execute(f"UPDATE team SET card{slot}_id = NULL WHERE card{slot}_id IN ({placeholders})", user_card_ids)
        
        # Удаляем записи из user_card
        cursor.execute("DELETE FROM user_card WHERE card_id = ?", (card_id,))
        user_cards_deleted = cursor.rowcount
        
        # Удаляем саму карточку
        cursor.execute("DELETE FROM card WHERE id = ?", (card_id,))
        cards_deleted = cursor.rowcount
        
        # Фиксируем изменения
        conn.commit()
        
        # Включаем обратно проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Закрываем соединение
        conn.close()
        
        return f"""
        <h1>Карточка успешно удалена</h1>
        <p>Карточка "{card_name}" (ID: {card_id}) была успешно удалена.</p>
        <p>Удалено {user_cards_deleted} экземпляров карточки у пользователей.</p>
        <p>Удалено {cards_deleted} карточек из базы данных.</p>
        <p><a href="http://127.0.0.1:5000/admin/cards">Вернуться к списку карточек</a></p>
        """
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        stack_trace = traceback.format_exc()
        
        # Если есть соединение с базой данных, закрываем его
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.close()
        except:
            pass
        
        return f"""
        <h1>Ошибка при удалении карточки</h1>
        <p>Произошла ошибка при удалении карточки с ID {card_id}:</p>
        <pre>{error_msg}</pre>
        <h2>Стек вызовов:</h2>
        <pre>{stack_trace}</pre>
        <p><a href="http://127.0.0.1:5000/admin/cards">Вернуться к списку карточек</a></p>
        """

if __name__ == '__main__':
    # Проверяем, передан ли ID карточки как аргумент командной строки
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        card_id = int(sys.argv[1])
        print(f"Удаление карточки с ID {card_id} через командную строку...")
        try:
            result = delete_card(card_id)
            print(result)
            sys.exit(0)
        except Exception as e:
            print(f"Ошибка: {str(e)}")
            sys.exit(1)
    else:
        # Запускаем веб-сервер
        print("Запуск веб-сервера для удаления карточек на порту 5001...")
        app.run(debug=True, port=5001)
