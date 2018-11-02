"""
Create new application skeleton.
"""

import glob
import os.path

from gettext import gettext as _
from string import Template

import six

from shelter.core.commands import BaseCommand, argument
from shelter.core.exceptions import CommandError


def substitute(template, mapping=None):
    """
    Render the template *template*. *mapping* is a :class:`dict` with
    values to add to the template.
    """
    if mapping is None:
        mapping = {}
    templ = Template(template)
    return templ.substitute(mapping)


def dirtree(path):
    """
    Find recursively and return all files and directories from
    the path *path*.
    """
    results = []
    for name in glob.glob(os.path.join(path, '*')):
        results.append(name)
        if os.path.isdir(name):
            results.extend(dirtree(name))
    return results


class StartProject(BaseCommand):
    """
    Management command which generates new application skeleton.
    """

    name = 'startproject'
    help = _('generate new application skeleton')
    arguments = (
        argument(
            'name',
            type=str, nargs=1,
            help=_('new project name')
        ),
        argument(
            '--author-name',
            type=str, dest='author_name', default='Your Name',
            help=_("author's name")
        ),
        argument(
            '--author-email',
            type=str, dest='author_email', default='your.email@example.com',
            help=_("author's e-mail")
        ),
    )
    settings_required = False

    def command(self):
        substitute_map = {
            'python': 'python3' if six.PY3 else 'python2',
            'package': self.context.config.args_parser.name[0],
            'author_name': self.context.config.args_parser.author_name,
            'author_email': self.context.config.args_parser.author_email,
        }

        skel_dir = os.path.join(os.path.dirname(__file__), 'startproject_skel')
        dest_dir = os.path.join(os.getcwd(), substitute_map['package'])

        if os.path.isdir(dest_dir):
            raise CommandError("%s already exists" % substitute_map['package'])
        else:
            os.mkdir(dest_dir)

        # Find all files in the project template
        suffix = '.template'
        suffix_len = len(suffix)
        prefix_len = len(skel_dir) + 1
        for src_name in dirtree(skel_dir):
            # Build destination name
            dst_name = substitute(
                os.path.join(dest_dir, src_name[prefix_len:]),
                substitute_map)
            if dst_name.endswith(suffix):
                dst_name = dst_name[:-suffix_len]
            # Copy source to destination
            if os.path.isdir(src_name) and not os.path.isdir(dst_name):
                # Make directory which doesn't exist
                os.mkdir(dst_name)
            else:
                # Copy file and adjust content
                with open(src_name, 'rt') as f_src,\
                        open(dst_name, 'wt') as f_dst:
                    f_dst.write(substitute(f_src.read(), substitute_map))
            # Keep permissions
            os.chmod(dst_name, os.stat(src_name).st_mode)
