
from shelter.commands import SHELTER_MANAGEMENT_COMMANDS


def test_shelter_management_commands():
    assert set(SHELTER_MANAGEMENT_COMMANDS) == set([
        'shelter.commands.devserver.DevServer',
        'shelter.commands.runserver.RunServer',
        'shelter.commands.shell.Shell',
        'shelter.commands.showconfig.ShowConfig',
        'shelter.commands.startproject.StartProject',
    ])
