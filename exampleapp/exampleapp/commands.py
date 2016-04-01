
from shelter.core.commands import BaseCommand


class HelloWorld(BaseCommand):

    name = "hello"
    help = "prints hello world"

    def command(self):
        self.stdout.write("Hello World!\n")
        self.stdout.flush()
