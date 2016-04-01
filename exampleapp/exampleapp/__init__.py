
import os

import shelter.main


def main():
    os.environ['SHELTER_SETTINGS_MODULE'] = 'exampleapp.settings'
    shelter.main.main()
