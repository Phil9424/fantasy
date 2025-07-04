from app import app, db, User

with app.app_context():
    # Check if the database file exists
    import os
    print(f"Database file exists: {os.path.exists('instance/mafia_fantasy.db')}")
    
    # Try to create tables
    try:
        db.create_all()
        print("Tables created successfully")
        
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        print("Tables in database:", inspector.get_table_names())
        
        # Try to add a test user
        test_user = User(username='test', email='test@example.com', is_admin=False, coins=100, points=0)
        test_user.set_password('test')
        db.session.add(test_user)
        db.session.commit()
        print("Test user added successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")
