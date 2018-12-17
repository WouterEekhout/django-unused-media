# -*- coding: utf-8 -*-

import os
import re
import shutil
import uuid
import datetime

import six
from django.conf import settings
from django.core.validators import EMPTY_VALUES

from .remove import remove_media
from .utils import get_file_fields

QUARANTINE_DIR = 'quarantine/'
DATETIME_FORMAT = '%Y-%m-%d_%H:%M'


def get_used_media():
    """
        Get media which are still used in models
    """

    media = set()

    for field in get_file_fields():
        is_null = {
            '%s__isnull' % field.name: True,
        }
        is_empty = {
            '%s' % field.name: '',
        }

        storage = field.storage

        for value in field.model.objects \
                .values_list(field.name, flat=True) \
                .exclude(**is_empty).exclude(**is_null):
            if value not in EMPTY_VALUES:
                media.add(storage.path(value))

    return media


def get_all_media(exclude=None, include_models=None):
    """
        Get all media from MEDIA_ROOT
    """

    if not exclude:
        exclude = []

    if not include_models:
        include_models = []

    media = set()

    valid_paths = get_valid_paths(include_models)

    for root, dirs, files in os.walk(six.text_type(settings.MEDIA_ROOT)):
        for name in files:
            path = os.path.abspath(os.path.join(root, name))
            relpath = os.path.relpath(path, settings.MEDIA_ROOT)
            is_excluded = False

            if not is_path_valid(valid_paths, path):
                is_excluded = True

            if not is_excluded:
                is_excluded = is_path_excluded(exclude, is_excluded, relpath)

            if not is_excluded:
                media.add(path)

    return media


def get_valid_paths(include_models):
    valid_paths = set()
    media_root = settings.MEDIA_ROOT

    if media_root.endswith('/'):
        media_root = media_root[:-1]

    for include_model in include_models:
        valid_paths.add("{0}/{1}".format(media_root, include_model))
    return valid_paths


def is_path_valid(valid_paths, path):
    if len(valid_paths) < 1:
        return True  # path is always valid if the user didn't set the include models

    is_valid = False

    for valid_path in valid_paths:
        if path.startswith(valid_path):
            is_valid = True
            break

    return is_valid


def is_path_excluded(exclude, is_excluded, relpath):
    for e in exclude:
        if re.match(r'^{0}'.format(re.escape(e).replace('\\*', '.*')), relpath):
            is_excluded = True
            break
    return is_excluded


def get_unused_media(exclude=None, include_models=None):
    """
        Get media which are not used in models
    """

    if not exclude:
        exclude = []

    exclude.append('quarantine')

    if not include_models:
        include_models = []

    all_media = get_all_media(exclude, include_models)
    used_media = get_used_media()

    return [x for x in all_media if x not in used_media]


def remove_unused_media():
    """
        Remove unused media
    """
    remove_media(get_unused_media())


def move_media_to_quarantine(files):
    """
        Moves the unused files from media dir to quarantine folder in the media dir
    :param files:
    :return:
    """
    ensure_dir(QUARANTINE_DIR)

    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d_%H:%M')

    for filename in files:
        origin = os.path.join(settings.MEDIA_ROOT, filename)

        destin = get_destination(filename, now_str)
        #destin = os.path.join(settings.MEDIA_ROOT, quarantine_dir, filename)

        ensure_dir(destin)
        shutil.move(origin, destin)


def get_destination(origin, now_str):
    origin = origin.replace(settings.MEDIA_ROOT, '')
    if origin.startswith('/'):
        origin = origin[1:]

    destin = os.path.join(settings.MEDIA_ROOT, QUARANTINE_DIR, now_str, origin)

    if os.path.exists(destin):
        extension = os.path.splitext(destin)[1]
        destin = destin.replace(extension, '')
        destin = "{0}_{1}{2}".format(destin, str(uuid.uuid4()), extension)

    return destin


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)

    if not os.path.exists(directory):
        os.makedirs(directory)


def clean_quarantine():
    # '%Y-%m-%d_%H:%M'
    now = datetime.datetime.now()

    listdirs = os.listdir(os.path.join(settings.MEDIA_ROOT, QUARANTINE_DIR))
    for name in listdirs:
        name_path = os.path.join(settings.MEDIA_ROOT, QUARANTINE_DIR, name)
        if os.path.isdir(name_path):

            try:
                dir_date = datetime.datetime.strptime(name, DATETIME_FORMAT)
            except ValueError:
                continue

            if dir_date < (now - datetime.timedelta(days=90)):
                print("Remove {0}".format(name))
                shutil.rmtree(name_path, ignore_errors=True)
