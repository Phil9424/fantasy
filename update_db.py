from app import app, db
from models import Pack, Transaction
import os

def create_tables():
    """Создает все таблицы, которых еще нет в базе данных"""
    with app.app_context():
        # Создаем все таблицы, определенные в моделях
        db.create_all()
        print("Все таблицы успешно созданы!")

def update_packs():
    """Добавляет тестовые пакеты в базу данных"""
    with app.app_context():
        # Проверяем, есть ли уже пакеты в базе
        if not Pack.query.first():
            # Создаем тестовый пак
            test_pack = Pack(
                name='Стандартный пак',
                description='Содержит случайные карты разной редкости',
                price=100,
                cards_count=3,
                min_rarity=1,
                max_rarity=5,
                prime_chance=0.1,
                is_active=True
            )
            db.session.add(test_pack)
            
            # Создаем премиум пак
            premium_pack = Pack(
                name='Премиум пак',
                description='Содержит карты высокой редкости и повышенный шанс прайм-карт',
                price=250,
                cards_count=3,
                min_rarity=3,
                max_rarity=5,
                prime_chance=0.25,
                is_active=True
            )
            db.session.add(premium_pack)
            
            # Создаем легендарный пак
            legendary_pack = Pack(
                name='Легендарный пак',
                description='Гарантированная карта 5-й редкости и высокий шанс прайм-карт',
                price=500,
                cards_count=3,
                min_rarity=4,
                max_rarity=5,
                prime_chance=0.5,
                is_active=True
            )
            db.session.add(legendary_pack)
            
            # Сохраняем изменения
            db.session.commit()
            print("Тестовые пакеты успешно добавлены!")
            return test_pack, premium_pack, legendary_pack
        else:
            print("Пакеты уже существуют, пропускаем создание.")
            return None, None, None

def update_db():
    """Основная функция обновления базы данных"""
    create_tables()
    test_pack, premium_pack, legendary_pack = update_packs()
    if test_pack and premium_pack and legendary_pack:
        print(f"Созданы тестовые паки: {test_pack.name}, {premium_pack.name}, {legendary_pack.name}")

if __name__ == '__main__':
    update_db()
