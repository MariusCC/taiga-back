# Copyright (C) 2014 Andrey Antukh <niwi@niwi.be>
# Copyright (C) 2014 Jesús Espino <jespinog@gmail.com>
# Copyright (C) 2014 David Barragán <bameda@dbarragan.com>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings

from taiga.base.utils.db import get_typename_for_model_instance
from taiga.projects.history import services as history_service

from . import tasks

watched_types = set([
    "userstories.userstory",
    "issues.issue",
    "tasks.task",
    "wiki.wiki_page",
    "milestones.milestone",
])


def _get_project_webhooks(project):
    webhooks = []
    # for webhook in project.webhooks.all()
    #     webhooks.append({
    #         "url": webhook.url,
    #         "key": webhook.key,
    #     })
    webhooks = [{
         "url": "dummy_url",
         "key": "dummy_key",
    }]
    return webhooks



def _get_last_change(obj):
    # TODO: Not working take the previous one, no the current one
    changes = history_service.get_history_queryset_by_model_instance(obj).order_by("-created_at")
    if changes:
        return changes[0]
    return None


def on_new_change(sender, instance, created, **kwargs):
    if not settings.WEBHOOKS_ENABLED:
        return None

    content_type = get_typename_for_model_instance(instance)

    if content_type != "history.historyentry":
        return None

    if history_service.is_hidden_snapshot(instance):
        return None

    model = history_service.get_model_from_key(instance.key)
    pk = history_service.get_pk_from_key(instance.key)
    obj = model.objects.get(pk=pk)

    webhooks = _get_project_webhooks(obj.project)

    for webhook in webhooks:
        if settings.CELERY_ENABLED:
            tasks.change_webhook.delay(webhook["url"], webhook["key"], obj, instance)
        else:
            tasks.change_webhook(webhook["url"], webhook["key"], obj, instance)

def on_save_any_model(sender, instance, created, **kwargs):
    if not settings.WEBHOOKS_ENABLED:
        return None

    content_type = get_typename_for_model_instance(instance)

    if content_type not in watched_types:
        return None

    webhooks = _get_project_webhooks(instance.project)

    if not created:
        return None

    for webhook in webhooks:
        if settings.CELERY_ENABLED:
            tasks.create_webhook.delay(webhook["url"], webhook["key"], instance)
        else:
            tasks.create_webhook(webhook["url"], webhook["key"], instance)


def on_delete_any_model(sender, instance, **kwargs):
    if not settings.WEBHOOKS_ENABLED:
        return None

    content_type = get_typename_for_model_instance(instance)

    if content_type not in watched_types:
        return None

    webhooks = get_project_webhooks(instance.project)

    for webhook in webhooks:
        if settings.CELERY_ENABLED:
            tasks.create_webhook.delay(webhook["url"], webhook["key"], instance)
        else:
            tasks.create_webhook(webhook["url"], webhook["key"], instance)
