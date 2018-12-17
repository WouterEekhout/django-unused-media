# -*- coding: utf-8 -*-

import mock
import six

from preggy import expect
from django.core.management import call_command

from .base import BaseTestCase


class TestManagementCommand(BaseTestCase):
    def test_command_call(self):
        expect(call_command('cleanup_unused_media', interactive=False)).Not.to_be_an_error()

    def test_command_nothing_to_delete(self):
        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=False, stdout=stdout)
        expect(stdout.getvalue().split('\n'))\
            .to_include(u'Nothing to do. Exit')

    def test_command_not_interactive(self):
        self._media_create('file.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=False, stdout=stdout)
        expect(stdout.getvalue().split('\n'))\
            .to_include(u'Placed {} to quarantine'.format(self._media_abs_path(u'file.txt')))\
            .to_include(u'Done. Total files placed in quarantine: 1')

        expect(self._media_exists('file.txt')).to_be_false()

    @mock.patch('six.moves.input', return_value='n')
    def test_command_interactive_n(self, mock_input):
        self._media_create(u'file.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=True, stdout=stdout)
        expect(stdout.getvalue().split('\n'))\
            .to_include(u'Interrupted by user. Exit.')

        expect(self._media_exists(u'file.txt')).to_be_true()

    @mock.patch('six.moves.input', return_value='Y')
    def test_command_interactive_y(self, mock_input):
        self._media_create(u'file.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=True, stdout=stdout)
        expect(stdout.getvalue().split('\n')) \
            .to_include(u'Placed {} to quarantine'.format(self._media_abs_path(u'file.txt'))) \
            .to_include(u'Done. Total files placed in quarantine: 1')

        expect(self._media_exists(u'file.txt')).to_be_false()

    @mock.patch('six.moves.input', return_value='Y')
    def test_command_interactive_y_with_ascii(self, mock_input):
        self._media_create(u'Тест.txt')

        expected_string = u'{}'.format(self._media_abs_path(u'Тест.txt'))
        if six.PY2:
            expected_string = expected_string.encode('utf-8')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=True, stdout=stdout)
        expect(stdout.getvalue().split('\n')) \
            .to_include(expected_string) \
            .to_include(u'Done. Total files placed in quarantine: 1')

        expect(self._media_exists(u'Тест.txt')).to_be_false()

    @mock.patch('django_unused_media.management.commands.cleanup_unused_media.remove_empty_dirs')
    def test_command_do_not_remove_dirs(self, mock_remove_empty_dirs):
        self._media_create(u'sub1/sub2/sub3/notused.txt')

        call_command('cleanup_unused_media', interactive=False)

        mock_remove_empty_dirs.assert_not_called()

    @mock.patch('django_unused_media.management.commands.cleanup_unused_media.remove_empty_dirs')
    def test_command_remove_dirs(self, mock_remove_empty_dirs):
        self._media_create(u'sub1/sub2/sub3/notused.txt')

        call_command('cleanup_unused_media', interactive=False, remove_empty_dirs=True)

        mock_remove_empty_dirs.assert_called_once()

    def test_command_dry_run(self):
        self._media_create('file.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=False, dry_run=True, stdout=stdout)
        expect(stdout.getvalue().split('\n')) \
            .to_include(self._media_abs_path(u'file.txt')) \
            .to_include(u'Total files will be placed in quarantine: 1') \
            .to_include(u'Dry run. Exit.')

        expect(self._media_exists('file.txt')).to_be_true()

    @mock.patch('six.moves.input', return_value='Y')
    def test_command_interactive_y_verbosity_0(self, mock_input):
        self._media_create(u'file.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', interactive=True, stdout=stdout, verbosity=0)
        expect(stdout.getvalue().split('\n')) \
            .Not.to_include(u'Files to place in quarantine:') \
            .Not.to_include(self._media_abs_path(u'file.txt')) \
            .Not.to_include(u'Remove {}'.format(self._media_abs_path(u'file.txt'))) \
            .to_include(u'Done. Total files placed in quarantine: 1')

        expect(self._media_exists(u'file.txt')).to_be_false()

    def test_command_show_possible_models(self):
        stdout = six.StringIO()
        call_command('cleanup_unused_media', show_possible_models=True, stdout=stdout, verbosity=0)
        expect(stdout.getvalue().split('\n')) \
            .to_include(u'Possible models are:') \
            .to_include(u'tests')

    def test_command_include_models(self):
        self._media_create(u'tests/include_models.txt')
        self._media_create(u'files/include_models.txt')

        stdout = six.StringIO()
        call_command('cleanup_unused_media', include_models=['tests'], stdout=stdout,
                     interactive=False)

        expect(self._media_exists(u'tests/include_models.txt')).to_be_false()
        expect(self._media_exists(u'files/include_models.txt')).to_be_true()

    def test_command_include_models_invalid_model(self):
        stdout = six.StringIO()
        call_command('cleanup_unused_media', include_models=['non_existing_model'],
                     stdout=stdout, interactive=False)

        expect(stdout.getvalue().split('\n')) \
            .to_include(u'Stopped processing. Incorrect input of the --include-models argument. '
                        u'Fix the errors and run the task again.') \
            .to_include(u'Possible options for --include-models are: ') \
            .to_include(u'tests')
