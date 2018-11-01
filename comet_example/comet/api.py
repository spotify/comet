# Copyright 2018 Spotify AB. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example Comet API"""

import logging

from comet_core.api import CometApi
from flask import Response, request

LOG = logging.getLogger(__name__)

# configuration, you might want to read this from a config file instead
CONFIG = {
    'cors_origins': [],
    'database_uri': 'sqlite:///comet-example.db',
    'host': '0.0.0.0',
    'port': 5000,
    'unsafe_skip_authorization': True,  # /!\ WARNING, using unauthenticated API calls for this example /!\
}

# initialize the API application
API = CometApi(cors_origins=CONFIG.get('cors_origins'),
               database_uri=CONFIG.get('database_uri'),
               host=CONFIG.get('host'),
               port=CONFIG.get('port'))


@API.register_auth()
def auth():
    """Checks authorization headers and verifies that proper credentials were provided.
    /!\ WARNING: this example does NOT do any authorization, you have to implement it here to secure access to your API.

    Returns:
        Union[List[str], flask.Response]: list of authenticated usernames or a HTTP 401 Response in case of no or
            invalid authorization header provided
    """
    if CONFIG.get('unsafe_skip_authorization', False):
        return ['example-resource-owner@example.com']

    LOG.debug('Checking authorization header...')
    authz_header = request.headers.get('Authorization')

    if not authz_header:
        return Response('No Authorization header provided', 401,
                        {'WWW-Authenticate': 'Bearer realm="Login Required"'})

    # Example code to illustrate how you could implement authorization and authentication:
    # authenticated_user = validate_authz_header_and_get_username(authz_header)
    # if is_user_authorized_for_api(authenticated_user):
    #     return [authenticated_user]

    LOG.warning('Invalid OAuth2 credentials provided!')

    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Bearer realm="Login Required"'})


@API.register_hydrator()
def hydrate(event_records):
    """Enriches issues with additional data
    Args:
        event_records (List[comet_core.model.EventRecord]): list of EventRecords to hydrate 
    Returns:
        List[dict]: list of dictionaries with the keys fingerprint and details_html, event_metadata
    """
    results = []
    for rec in event_records:
        md = rec.event_metadata
        # create custom fields
        result = {
            'fingerprint': rec.fingerprint,
            'details': f'{md.get("source_readable")} alert for owner {rec.owner}: {md.get("resource_readable")} has the'
                       f' following issue: {md.get("issue_type_readable")}',
        }
        # add all metadata fields
        result.update(rec.event_metadata)
        results.append(result)

    return results


# create the API app
APP = API.create_app()
