import configparser
from pathlib import Path


def parse_key_codes(param: str) -> dict[int, str]:
    """
    Parse the specified keycodes parameter.
    :param param: The parameter.
    :return: The parsed keycodes and their associated labels.
    """

    # Split the param into pairs.
    pairs: list[list[str]] = [segment.split(':', 2) for segment in param.split(',')]
    if any(len(pair) < 2 for pair in pairs):
        raise Exception(f'Invalid keycodes, must consist of key-value pairs.')

    # Turn the pairs into a dict.
    return dict([(int(pair[0]), pair[1]) for pair in pairs])


# Read the configuration.
config = configparser.ConfigParser()
config.read(['/etc/camera-connect/config.ini', 'config.ini'])

# Trigger configuration.
KEY_CODES: dict[int, str] = parse_key_codes(config.get('Trigger', 'KeyCodes'))
GRAB: bool = config.getboolean('Trigger', 'Grab')

# General configuration.
SPOOL_PATH: Path = Path(config.get('General', 'SpoolPath'))
WEBCAM_URL: str = config.get('General', 'WebcamURL', fallback='<video0>')
AUDIO_DEVICE: str = config.get('General', 'AudioDevice', fallback='default')

# Glide configuration
GLIDE_API_KEY: str = config.get('Glide', 'APIKey')
GLIDE_APP_ID: str = config.get('Glide', 'AppID')

# Webhook configuration.
WEBHOOK_URL: str = config.get('Webhook', 'URL')
WEBHOOK_TOKEN: str = config.get('Webhook', 'Token')
