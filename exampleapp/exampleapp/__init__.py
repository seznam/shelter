
import os.path

import shelter.main


def main():
    os.environ['SHELTER_SETTINGS_MODULE'] = 'exampleapp.settings'
    os.environ['SHELTER_CONFIG_FILENAME'] = os.path.join(
        os.path.dirname(__file__), os.pardir, 'conf', 'exampleapp.conf')
    shelter.main.main()
