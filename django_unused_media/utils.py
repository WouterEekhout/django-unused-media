# -*- coding: utf-8 -*-

from django.apps import apps
from django.db import models


def verify_user_file_models(user_file_models):
    if not user_file_models:
        user_file_models = []

    file_models = set()
    for file_model in get_file_models():
        file_models.add(str(file_model))

    all_clear = True

    for user_file_model in user_file_models:
        if user_file_model not in file_models:
            # print("Error! Model {0} does not exist".format(user_file_model))
            all_clear = False

    return all_clear


def get_file_models():
    file_fields = get_file_fields()

    file_models = set()

    for file_field in file_fields:
        file_models.add(file_field.model._meta.app_label)

    return file_models


def get_file_fields():
    """
        Get all fields which are inherited from FileField
    """

    # get models

    all_models = apps.get_models()

    # get fields

    fields = []

    for model in all_models:
        for field in model._meta.get_fields():
            if isinstance(field, models.FileField):
                fields.append(field)

    return fields
