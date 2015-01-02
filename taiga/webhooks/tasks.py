# Copyright (C) 2013 Andrey Antukh <niwi@niwi.be>
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

import json

from taiga.base.utils.db import get_typename_for_model_instance
from taiga.celery import app

from .serializers import (UserStorySerializer, IssueSerializer, TaskSerializer,
                          WikiPageSerializer, MilestoneSerializer,
                          HistoryEntrySerializer)


def _serialize(obj):
    content_type = get_typename_for_model_instance(obj)

    if content_type == "userstories.userstory":
        return UserStorySerializer(obj).data
    elif content_type == "issues.issue":
        return IssueSerializer(obj).data
    elif content_type == "tasks.task":
        return TaskSerializer(obj).data
    elif content_type == "wiki.wiki_page":
        return WikiPageSerializer(obj).data
    elif content_type == "milestones.milestone":
        return MilestoneSerializer(obj).data
    elif content_type == "history.historyentry":
        return HistoryEntrySerializer(obj).data


def _get_type(obj):
    content_type = get_typename_for_model_instance(obj)
    return content_type.split(".")[1]


def _generate_signature(data, key):
    mac = hmac.new(secret, msg=data, digestmod=hashlib.sha1)
    return mac.hexdigest()


def _send_request(url, key, data):
    print(url, key, data)
    # serialized_data = json.dumps(data)
    # signature = _generate_signature(serialize_data, key)
    # headers = {
    #     "X-TAIGA-WEBHOOK-SIGNATURE": signature,
    # }
    # request.post(url, data=serialized_data, headers=headers)


@app.task
def change_webhook(url, key, obj, change):
    data = {}
    data['data'] = _serialize(obj)
    data['action'] = "create"
    data['type'] = _get_type(obj)
    data['change'] = _serialize(change)

    _send_request(url, key, data)


@app.task
def create_webhook(url, key, obj):
    data = {}
    data['data'] = _serialize(obj)
    data['action'] = "create"
    data['type'] = _get_type(obj)

    _send_request(url, key, data)


@app.task
def delete_webhook(url, key, obj):
    data = {}
    data['data'] = _serialize(obj)
    data['action'] = "delete"
    data['type'] = _get_type(obj)

    _send_request(url, key, data)
