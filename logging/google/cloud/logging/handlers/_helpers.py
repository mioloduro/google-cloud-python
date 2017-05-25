# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper functions for logging handlers."""

import math
import json

try:
    import flask
except ImportError:
    flask = None

from google.cloud.logging.handlers.middleware.request import RequestMiddleware

_FLASK_TRACE_HEADER = 'X_CLOUD_TRACE_CONTEXT'
_DJANGO_TRACE_HEADER = 'HTTP_X_CLOUD_TRACE_CONTEXT'

_EMPTY_TRACE_ID = 'None'


def format_stackdriver_json(record, message):
    """Helper to format a LogRecord in in Stackdriver fluentd format.

        :rtype: str
        :returns: JSON str to be written to the log file.
    """
    subsecond, second = math.modf(record.created)

    payload = {
        'message': message,
        'timestamp': {
            'seconds': int(second),
            'nanos': int(subsecond * 1e9),
        },
        'thread': record.thread,
        'severity': record.levelname,
    }

    return json.dumps(payload)


def get_trace_id_from_flask():
    """Get trace_id from flask request headers.

    :rtype: str
    :return: Trace_id in HTTP request headers.
    """
    if not flask or not flask.request:
        return _EMPTY_TRACE_ID

    header = flask.request.headers.get(_FLASK_TRACE_HEADER)

    if not header:
        return _EMPTY_TRACE_ID

    trace_id = header.split('/')[0]

    return trace_id


def get_trace_id_from_django():
    """Get trace_id from django request headers.

    :rtype: str
    :return: Trace_id in HTTP request headers.
    """
    request_middleware = RequestMiddleware()
    request = request_middleware.get_request()

    if not request:
        return _EMPTY_TRACE_ID

    try:
        header = request.META[_DJANGO_TRACE_HEADER]
    except KeyError:
        return _EMPTY_TRACE_ID

    trace_id = header.split('/')[0]

    return trace_id


def get_trace_id():
    """Helper to get trace_id from web application request header.

    :rtype: str
    :returns: Trace_id in HTTP request headers.
    """
    checkers = [get_trace_id_from_django, get_trace_id_from_flask]

    for checker in checkers:
        trace_id = checker()
        if trace_id is not _EMPTY_TRACE_ID:
            return trace_id

    return trace_id
