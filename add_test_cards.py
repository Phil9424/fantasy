from app import app, db, Card
import os

# Список тестовых карт разной редкости
test_cards = [
    # Обычные карты (редкость 1)
    {'name': 'Мирный житель', 'image': 'civilian1.png', 'rarity': 1, 'is_prime': False, 'base_points': 10},
    {'name': 'Доктор', 'image': 'doctor.png', 'rarity': 1, 'is_prime': False, 'base_points': 15},
    {'name': 'Шериф', 'image': 'sheriff.png', 'rarity': 1, 'is_prime': False, 'base_points': 15},
    {'name': 'Детектив', 'image': 'detective.png', 'rarity': 1, 'is_prime': False, 'base_points': 12},
    {'name': 'Журналист', 'image': 'journalist.png', 'rarity': 1, 'is_prime': False, 'base_points': 10},
    
    # Необычные карты (редкость 2)
    {'name': 'Телохранитель', 'image': 'bodyguard.png', 'rarity': 2, 'is_prime': False, 'base_points': 20},
    {'name': 'Медиум', 'image': 'medium.png', 'rarity': 2, 'is_prime': False, 'base_points': 22},
    {'name': 'Адвокат', 'image': 'lawyer.png', 'rarity': 2, 'is_prime': False, 'base_points': 18},
    {'name': 'Судья', 'image': 'judge.png', 'rarity': 2, 'is_prime': False, 'base_points': 25},
    {'name': 'Мститель', 'image': 'avenger.png', 'rarity': 2, 'is_prime': False, 'base_points': 20},
    
    # Редкие карты (редкость 3)
    {'name': 'Мафиози', 'image': 'mafioso.png', 'rarity': 3, 'is_prime': False, 'base_points': 30},
    {'name': 'Дон мафии', 'image': 'don.png', 'rarity': 3, 'is_prime': False, 'base_points': 35},
    {'name': 'Маньяк', 'image': 'maniac.png', 'rarity': 3, 'is_prime': False, 'base_points': 32},
    {'name': 'Якудза', 'image': 'yakuza.png', 'rarity': 3, 'is_prime': False, 'base_points': 33},
    {'name': 'Комиссар', 'image': 'commissar.png', 'rarity': 3, 'is_prime': False, 'base_points': 35},
    
    # Эпические карты (редкость 4)
    {'name': 'Крестный отец', 'image': 'godfather.png', 'rarity': 4, 'is_prime': False, 'base_points': 45},
    {'name': 'Экстрасенс', 'image': 'psychic.png', 'rarity': 4, 'is_prime': False, 'base_points': 42},
    {'name': 'Ассасин', 'image': 'assassin.png', 'rarity': 4, 'is_prime': False, 'base_points': 48},
    {'name': 'Вор в законе', 'image': 'thief_in_law.png', 'rarity': 4, 'is_prime': False, 'base_points': 44},
    {'name': 'Шпион', 'image': 'spy.png', 'rarity': 4, 'is_prime': False, 'base_points': 40},
    
    # Легендарные карты (редкость 5)
    {'name': 'Босс мафии', 'image': 'boss.png', 'rarity': 5, 'is_prime': True, 'base_points': 60},
    {'name': 'Мастер игры', 'image': 'gamemaster.png', 'rarity': 5, 'is_prime': True, 'base_points': 65},
    {'name': 'Призрак', 'image': 'ghost.png', 'rarity': 5, 'is_prime': True, 'base_points': 58},
    {'name': 'Джокер', 'image': 'joker.png', 'rarity': 5, 'is_prime': True, 'base_points': 62},
    {'name': 'Хакер', 'image': 'hacker.png', 'rarity': 5, 'is_prime': True, 'base_points': 55},
]

# Создаем заглушки для изображений карт
def create_placeholder_images():
    uploads_dir = 'static/uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    for card in test_cards:
        image_path = os.path.join(uploads_dir, card['image'])
        if not os.path.exists(image_path):
            # Создаем пустой файл
            with open(image_path, 'w') as f:
                f.write('')

# Добавляем карты в базу данных
def add_cards_to_db():
    with app.app_context():
        # Проверяем, есть ли уже карты в базе
        if Card.query.count() > 0:
            print('В базе данных уже есть карты. Пропускаем добавление тестовых карт.')
            return
        
        # Добавляем карты
        for card_data in test_cards:
            card = Card(
                name=card_data['name'],
                image=card_data['image'],
                rarity=card_data['rarity'],
                is_prime=card_data['is_prime'],
                base_points=card_data['base_points']
            )
            db.session.add(card)
        
        # Сохраняем изменения
        db.session.commit()
        print(f'Добавлено {len(test_cards)} тестовых карт в базу данных.')

if __name__ == '__main__':
    create_placeholder_images()
    add_cards_to_db()
