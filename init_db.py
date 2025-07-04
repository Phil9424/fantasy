from app import app, db, User, Card, UserCard, Team, Tournament
import os

def init_db():
    with app.app_context():
        # Ensure the instance folder exists
        instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        
        # Drop all tables if they exist
        db.drop_all()
        
        # Create all database tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='SM',
            email='admin@mafia-fantasy.ru',
            is_admin=True,
            coins=1000,
            points=0
        )
        admin.set_password('admin')  # Set a secure password in production
        db.session.add(admin)
        
        # Commit changes
        db.session.commit()
        
        # Verify the database file was created
        db_path = os.path.join(instance_path, 'mafia_fantasy.db')
        if os.path.exists(db_path):
            print(f"Database created at: {db_path}")
        else:
            print("Warning: Database file was not created!")
        
        print("Database initialized successfully!")
        print(f"Admin user created with username: {admin.username}")
        print(f"Admin email: {admin.email}")
        print(f"Admin password: admin (please change this after login)")

if __name__ == '__main__':
    init_db()
