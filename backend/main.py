from flask import Flask
from flask_cors import CORS
import os
from routes import register_routes
from database import init_db
from models import Photo  # Import models to register them


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Initialize database
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    return app


if __name__ == '__main__':
    # Check required environment variables
    required_env_vars = ["GCP_PROJECT_ID", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
    
    app = create_app()
    
    # Create database tables
    with app.app_context():
        from database import db
        db.create_all()
        print("Database tables created successfully!")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
