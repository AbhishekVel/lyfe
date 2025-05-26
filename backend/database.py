import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app"""
    
    # Database configuration
    database_url = os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:password123@postgres:5432/lyfe'
    )
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db 