from wsgi import app, db, migrate
from flask_migrate import upgrade, migrate as migrate_db, init, stamp

def init_migrations():
    with app.app_context():
        init()
        stamp()
        print("Migrations initialized")

def run_migrations():
    with app.app_context():
        migrate_db(message='Add Pack model')
        upgrade()
        print("Migrations applied")

if __name__ == '__main__':
    init_migrations()
    run_migrations()
