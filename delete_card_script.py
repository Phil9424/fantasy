#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для принудительного удаления карточки из базы данных.
Использует прямые SQL-запросы, минуя Flask и ORM.
"""

import sqlite3
import sys
import os

def delete_card(card_id):
    """Удаляет карточку и все связанные записи из базы данных."""
    
    # Путь к базе данных
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'mafia_fantasy.db')
    
    if not os.path.exists(db_path):
        print(f"Ошибка: База данных не найдена по пути {db_path}")
        return False
    
    print(f"Подключение к базе данных: {db_path}")
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Отключаем проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Начинаем транзакцию
        print(f"Начало удаления карточки с ID: {card_id}")
        
        # Проверяем, существует ли карточка
        cursor.execute("SELECT id, name FROM card WHERE id = ?", (card_id,))
        card = cursor.fetchone()
        
        if not card:
            print(f"Ошибка: Карточка с ID {card_id} не найдена")
            return False
        
        print(f"Найдена карточка: ID={card[0]}, Имя={card[1]}")
        
        # Находим все user_card, связанные с этой карточкой
        cursor.execute("SELECT id FROM user_card WHERE card_id = ?", (card_id,))
        user_cards = cursor.fetchall()
        user_card_ids = [uc[0] for uc in user_cards]
        
        print(f"Найдено {len(user_cards)} экземпляров карточки у пользователей")
        
        # Очищаем ссылки на эти карточки в командах
        if user_card_ids:
            for slot in range(1, 5):  # В таблице team есть только 4 слота: slot1_card_id, slot2_card_id, slot3_card_id, slot4_card_id
                query = f"UPDATE team SET slot{slot}_card_id = NULL WHERE slot{slot}_card_id IN ({','.join(['?'] * len(user_card_ids))})"
                cursor.execute(query, user_card_ids)
                print(f"Очищены ссылки в слоте {slot} команд: {cursor.rowcount} обновлено")
        
        # Удаляем записи из user_card
        cursor.execute("DELETE FROM user_card WHERE card_id = ?", (card_id,))
        print(f"Удалено {cursor.rowcount} записей из user_card")
        
        # Удаляем саму карточку
        cursor.execute("DELETE FROM card WHERE id = ?", (card_id,))
        print(f"Удалено {cursor.rowcount} записей из card")
        
        # Фиксируем изменения
        conn.commit()
        print("Изменения успешно зафиксированы")
        
        # Включаем обратно проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = ON")
        
        print(f"Карточка с ID {card_id} успешно удалена")
        return True
        
    except Exception as e:
        print(f"Ошибка при удалении карточки: {str(e)}")
        if conn:
            conn.rollback()
            cursor.execute("PRAGMA foreign_keys = ON")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python delete_card_script.py <ID карточки>")
        sys.exit(1)
    
    try:
        card_id = int(sys.argv[1])
    except ValueError:
        print("Ошибка: ID карточки должен быть числом")
        sys.exit(1)
    
    success = delete_card(card_id)
    sys.exit(0 if success else 1)
