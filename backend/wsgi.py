import os
from backend.config import DevelopmentConfig, TestingConfig, ProductionConfig
from backend.app import create_app

def get_config_class():
    """Return the appropriate config class based on FLASK_ENV environment variable."""
    env = os.getenv('FLASK_ENV', 'development')
    config_map = {
        'production': ProductionConfig,
        'testing': TestingConfig,
        'development': DevelopmentConfig,
    }
    return config_map.get(env, DevelopmentConfig)

# Create the Flask application with the selected config
app = create_app(config_class=get_config_class())

if __name__ == '__main__':
    app.run()