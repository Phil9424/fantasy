from app import app, db
from models import UserCard

def apply_migration():
    with app.app_context():
        # Add the new column using raw SQL
        db.engine.execute('ALTER TABLE user_card ADD COLUMN listed_at DATETIME')
        print("Successfully added 'listed_at' column to user_card table")

if __name__ == '__main__':
    apply_migration()
