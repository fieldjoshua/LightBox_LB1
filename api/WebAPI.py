"""
Flask web application for LED matrix control panel
Provides real-time control and monitoring interface
"""

from flask import Flask
from flask_socketio import SocketIO
import os
import sys
from api.routes import api_blueprint


def create_app(led_controller=None):
    """
    Creates and configures the Flask application and SocketIO server.
    """
    # Add the project root to the Python path
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    )

    app = Flask(
        __name__,
        template_folder='../web/templates',
        static_folder='../web/static'
    )

    # Configuration
    app.config['UPLOAD_FOLDER'] = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'scripts')
    )
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['SECRET_KEY'] = 'lightbox_secret_key'
    
    # Initialize extensions
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Attach the LED controller to the app context
    app.led_controller = led_controller
    
    # Register blueprints
    app.register_blueprint(api_blueprint)
    
    return app, socketio