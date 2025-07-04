from app import app, db, create_admin
from flask_migrate import Migrate

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Register CLI commands
@app.cli.command('create-admin')
def create_admin_command():
    """CLI command to create an admin user"""
    with app.app_context():
        create_admin()
        print("Admin user created successfully!")

if __name__ == "__main__":
    app.run(debug=True)
