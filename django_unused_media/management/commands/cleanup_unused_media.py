# -*- coding: utf-8 -*-

import six.moves
from django.conf import settings
from django.core.management.base import BaseCommand

from django_unused_media.cleanup import get_unused_media
from django_unused_media.remove import remove_empty_dirs, move_media_to_quarantine
from django_unused_media.utils import get_file_models, verify_user_file_models


class Command(BaseCommand):

    help = "Clean unused media files which have no reference in models"

    # verbosity
    # 0 means minimal output
    # 1 means normal output (default).
    # 2 means verbose output

    verbosity = 1

    def add_arguments(self, parser):

        parser.add_argument('-m', '--show-possible-models',
                            dest='show_possible_models',
                            action='store_true',
                            default=None,
                            help='Show the list of possible models for the --include-models '
                                 'argument')

        parser.add_argument('--noinput', '--no-input',
                            dest='interactive',
                            action='store_false',
                            default=True,
                            help='Do not ask confirmation')

        parser.add_argument('-e', '--exclude',
                            dest='exclude',
                            action='append',
                            default=[],
                            help='Exclude files by mask (only * is supported), can use multiple '
                                 '--exclude')

        parser.add_argument('-i', '--include-models',
                            dest='include_models',
                            action='append',
                            default=[],
                            help='Include only a specific list of models, can use multiple '
                                 '--include')

        parser.add_argument('--remove-empty-dirs',
                            dest='remove_empty_dirs',
                            action='store_false',
                            default=False,
                            help='Remove empty dirs after files cleanup')

        parser.add_argument('-n', '--dry-run',
                            dest='dry_run',
                            action='store_true',
                            default=False,
                            help='Dry run without any affect on your data')

    def info(self, message):
        if self.verbosity >= 0:
            self.stdout.write(message)

    def debug(self, message):
        if self.verbosity >= 1:
            self.stdout.write(message)

    def _show_files_to_delete(self, unused_media):
        self.debug('Files to place in quarantine:')

        for f in unused_media:
            self.debug(f)

        self.info('Total files will be placed in quarantine: {}'.format(len(unused_media)))

    def _print_file_models(self):
        file_models = get_file_models()
        for file_model in file_models:
            self.info(file_model)

    def handle(self, *args, **options):

        if 'verbosity' in options:
            self.verbosity = options['verbosity']

        if options.get('show_possible_models'):
            self.info("Possible models are:")
            self._print_file_models()
            return

        if options.get('include_models'):
            all_clear = verify_user_file_models(options.get('include_models'))
            if not all_clear:
                self.info("Stopped processing. Incorrect input of the --include-models argument. "
                          "Fix the errors and run the task again.")
                self.info("Possible options for --include-models are: ")
                self._print_file_models()
                return

        unused_media = get_unused_media(options.get('exclude') or [], options.get(
            'include_models') or [])

        if not unused_media:
            self.info('Nothing to do. Exit')
            return

        if options.get('dry_run'):
            self._show_files_to_delete(unused_media)
            self.info('Dry run. Exit.')
            return

        if options.get('interactive'):
            self._show_files_to_delete(unused_media)

            # ask user
            question = 'Are you sure you want to place {} unused files in quarantine? (y/N)'.format(len(
                unused_media))

            if six.moves.input(question).upper() != 'Y':
                self.info('Interrupted by user. Exit.')
                return

        self.debug('Moving files to quarantine')
        move_media_to_quarantine(unused_media)
        for f in unused_media:
            self.debug('Placed {} to quarantine'.format(f))

        if options.get('remove_empty_dirs'):
            remove_empty_dirs()

        self.info('Done. Total files placed in quarantine: {}'.format(len(unused_media)))
