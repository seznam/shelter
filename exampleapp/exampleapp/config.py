
from shelter.contrib.config.iniconfig import IniConfig


class Config(IniConfig):

    @property
    def secret_key(self):
        return self.settings.SECRET_KEY
