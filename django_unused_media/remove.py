# -*- coding: utf-8 -*-

import os
import shutil

from django.conf import settings


def move_media_to_quarantine(files):
    """
        Moves the unused files from media dir to quarantine folder in the media dir
    :param files:
    :return:
    """
    quarantine_dir = 'quarantine/'
    ensure_dir(quarantine_dir)
    for filename in files:
        origin = os.path.join(settings.MEDIA_ROOT, filename)

        filename = filename.replace(settings.MEDIA_ROOT, '')
        if filename.startswith('/'):
            filename = filename[1:]

        destin = os.path.join(settings.MEDIA_ROOT, quarantine_dir, filename)

        ensure_dir(destin)
        shutil.move(origin, destin)


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)


def remove_media(files):
    """
        Delete file from media dir
    """
    for filename in files:
        os.remove(os.path.join(settings.MEDIA_ROOT, filename))


def remove_empty_dirs(path=None):
    """
        Recursively delete empty directories; return True if everything was deleted.
    """

    if not path:
        path = settings.MEDIA_ROOT

    if not os.path.isdir(path):
        return False

    listdir = [os.path.join(path, filename) for filename in os.listdir(path)]

    if all(list(map(remove_empty_dirs, listdir))):
        os.rmdir(path)
        return True
    else:
        return False
