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

"""Example Comet application."""

import logging
from datetime import timedelta

from comet_common.comet_input_google_pubsub import PubSubInput
from comet_common.comet_parser_detectify import DetectifySchema
from comet_common.comet_parser_forseti import ForsetiSchema
from comet_core import Comet
from comet_core.fingerprint import comet_event_fingerprint

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)  # you might want to change the level to logging.INFO when running in production

LOG.info('Setting up Comet...')

APP = Comet(database_uri='sqlite:///comet-example.db')  # use any other database backend here that SQLAlchemy supports

LOG.info('Created app instance.')


# Outputs
def send_email(recipient, subject, body):
    """Send email to recipient with given subject and body - implement your email sending or other outputs channel here.

    Args:
      recipient (str): recipient email address
      subject (str): email subject line
      body (str): email body
    """
    LOG.debug(f'Sending email to {recipient} with subject {subject}: {body[:100]}...')
    # Implement your email sending here.


# Inputs
APP.register_input(PubSubInput,
                   subscription_name='projects/comet-example-project/subscriptions/comet-example-subscription')

LOG.info('Registered inputs.')

# Parsers
APP.register_parser('forseti', ForsetiSchema)
APP.register_parser('detectify', DetectifySchema)

LOG.info('Registered parsers.')

# Override configuration
APP.set_config('forseti', {'wait_for_more': timedelta(minutes=2)})


# Hydrators
@APP.register_hydrator('forseti')
def hydrate_forseti(event):
    """Hydrator for forseti events, enriching them with owner, a fingerprint and metadata.
    
    Args:
      event (comet_core.app.EventContainer): the incoming event to hydrate
    """
    msg = event.message

    event.set_owner(f"{msg.get('project_owner')}@example.com")
    event.set_fingerprint(comet_event_fingerprint(data_dict=msg,
                                                  blacklist=['id', 'rule_index'],
                                                  prefix='forseti_'))

    # arbitrary metadata
    event.set_metadata({
        'issue_type': msg.get('resource'),
        'source_readable': 'GCP Configuration Scanner',
        'resource': msg['project_id'] + '/' + msg['resource_id'],
        'resource_readable':
            f"{msg.get('resource_type')} {msg.get('resource_id')} (in {msg.get('project_id')})",
        'issue_type_readable': {
            'policy_violations': 'GCP project owner outside org',
            'buckets_acl_violations': 'Storage bucket shared too widely',
            'cloudsql_acl_violations': 'CloudSQL open to the public internet',
            'bigquery_acl_violations': 'BigQuery data shared too widely',
        }.get(msg.get('resource'), msg.get('resource'))
    })


def get_owner_email_from_domain(domain):
    """Look up the owner email address for a given domain.

    Returning dummy addresses here - implement your own domain->email lookup here.
    Returns:
        str: email address
    """
    email = {
        'example-domain-a.example.com': 'owner-a@example.com',
        'example-domain-b.example.com': 'owner-b@example.com',
    }.get(domain, 'example-resource-owner@example.com')
    return email


@APP.register_hydrator('detectify')
def hydrate_detectify(event):
    """Hydrator for detectify events, enriching them with owner, a fingerprint and metadata.
    
    Args:
      event (comet_core.app.EventContainer): the incoming event to hydrate
    """
    msg = event.message

    event.set_owner(get_owner_email_from_domain(msg['domain']))

    event.set_fingerprint('detectify_' + msg['payload']['signature'])

    # arbitrary metadata
    event.set_metadata({
        'issue_type': msg['payload']['title'],
        'source_readable': 'Web Security Scanner',
        'resource': msg['domain'],
        'resource_readable': msg['domain'],
        'issue_type_readable': msg['payload']['title']
    })


def make_email_body_from_events(events):
    """For a list of events, craft an email body.

    Args:
        events List[comet_core.app.EventContainer]: list of events to alert about
    Returns:
        str: an nicely formatted email body
    """
    return 'Example email body - implement your email rendering here, for example using http://jinja.pocoo.org/'


# Routers
@APP.register_router()
def route(source_type, owner_email, events):
    """Route events to output channels based on their source type and owner.

    Args:
      source_type (str): the source type of the events to route
      owner_email (str): email address of the resource owner
      events (List[comet_core.app.EventContainer]): list of events to alert about
    """
    subject = {
        'detectify': 'Your website has a security vulnerability!',
        'forseti': 'Your GCP project is insecurely configured',
    }.get(source_type, 'Security issue found')

    body = make_email_body_from_events(events)
    send_email(owner_email, subject, body)


@APP.register_escalator()
def escalate(source_type, events):  # pylint: disable=missing-docstring
    """Escalates the given events based on their source type.

    Args:
      source_type (str): the source type of the events to escalate
      events (List[comet_core.app.EventContainer]): list of events to escalate
    """
    subject = f'Comet escalations: {len(events)} events have not been acted on'
    recipient = {
        'detectify': 'web-team@example.com',
    }.get(source_type, 'security-team@example.com')
    body = make_email_body_from_events(events)
    send_email(recipient, subject, body)


LOG.info('Registered hydrators, routers and escalator.')

LOG.info('Starting the Comet app...')
APP.run()
