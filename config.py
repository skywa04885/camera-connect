import configparser
from pathlib import Path

# Read the configuration.
config = configparser.ConfigParser()
config.read(['/etc/camera-connect/config.ini', 'config.ini'])

# Trigger configuration.
KEY_CODE: int = config.getint('Trigger', 'KeyCode')
GRAB: bool = config.getboolean('Trigger', 'Grab')

# General configuration.
SPOOL_PATH: Path = Path(config.get('General', 'SpoolPath'))
WEBCAM_URL: str = config.get('General', 'WebcamURL', fallback='<video0>')
DEVICE_IDENTIFIER: str = config.get('General', 'DeviceIdentifier')

# Glide configuration
GLIDE_API_KEY: str = config.get('Glide', 'APIKey')
GLIDE_APP_ID: str = config.get('Glide', 'AppID')

# Webhook configuration.
WEBHOOK_URL: str = config.get('Webhook', 'URL')
WEBHOOK_TOKEN: str = config.get('Webhook', 'Token')
