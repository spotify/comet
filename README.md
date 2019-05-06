Comet is an alert distribution framework which allows you to distribute alerts all the way to the resource owner with customizable owner lookup, de-duplication, alert formatting as well as automated follow-up and metrics.

Built with ❤️ at Spotify

# Structure

Comet is built as a collection of plugins that can be combined to build your own application. This repository hosts an example application using the two public Comet libraries comet-core and comet-common.

## comet core
https://github.com/spotify/comet-core

Core plugin providing the comet app (including data store, event batching and grouping by owner) and the comet API. 

## comet-common
https://github.com/spotify/comet-common

Common plugin with input plugins (for example for Google pubsub) and parsers (for example for Detectify and Forseti).

# Background
In order to maintain security of all different parts of Spotify's infrastructure, the Security team has been employing automated security scanning, such as Forseti, Detectify, and customized scanners that we've built in house.

The open source and commercial scanners are usually good at what they do, namely scanning, but have less functionality for directing the alerts and reports to the right place. As such this mostly ended up as manual work for the security teams.

For our in-house made scanners we noticed that we tended to re-write the code for finding the right owners and cobbling together templates and email sending code to notify the correct owner, every implementation with its own set of bugs.

We also realized that these alerts are a great source of data and can be used to better direct our teaching efforts where they do the most impact. Moreover by looking at what areas of the company are not getting alerts we can learn about where we need to implement better scanning capabilities.

This is where Comet comes into the picture. We wanted a robust and scalable alert handling tool, that would automate away a lot of the manual work and at the same time provide us with metrics and an overview of our infrastructure security. The design is modularised to allow for others to tailor Comet to their specific needs and context. 


# Feature description
Below are a bunch of features that are configurable per alert source. 

   Email Customization: Each type of alert by customized per a alert source. You can put different instructions into the email depending on the alert.

   Batching: For every alert type we have a configurable batching time. This means we will wait to send out emails until that amount of time has passed. This is useful for scans that run at a set time and produce many alerts. A team will get a single email instead of a email for each problem.

   Snoozing: A alert for a single thing will only go out once over a configurable time span for each alert. This means you will not get a email every day about the same bug.
   
   Whitelisting: Developers can whitelist an alert. They can chose different reasons for whitelisting including because an alert is false positive or because they alert thing they were alerted about is an excepted business risk.

   Escalations: You can decide to whom and when to escalate alerts. For example some alerts you might want to escalate right away, others you might never want to excilate. To whom is a single static field. You can configure it so each alert owner gets escalated to for their own scanners.

We have also build some plugins that are useful for tools that other people might also be using. 

   GCP Pubsub: Right now we ingest the alerts through Google pubsub. If you are using GCP then you can use this plugin as the input plugin.

   Detectify: Detectify is a web scanning tool we use at Spotify. If you are also a customer then this will take the detectify alerts and send them into the comet pipeline.

   Forseti: This will take Forseti alerts and send them through comet. This allows tracking of metrics for comet.


# Quick Start

In the `comet_example` folder you find a fully functional example of how to build a Comet application and run it. 
To test it out, do the following:


## Clone the example repository


Clone this repository:

```bash
git clone https://github.com/spotify/comet
```

Change to the example directory, all further steps are performed from that directory if it is not stated otherwise.

```bash
cd comet/comet_example
```


## Setup a Google cloud pubsub emulator

The example Comet app uses a Google cloud pubsub input plugin to receive alert messages, so for testing purposes
we will run a Google pubsub emulator locally to deliver test messages to the Comet app. To setup the emulator follow
these steps:

Make sure you have the [`gcloud` command line tool](https://cloud.google.com/sdk/gcloud/) installed.

Then install and start the emulator: 

```bash
gcloud components install pubsub-emulator
gcloud components update
gcloud beta emulators pubsub start
```

Check that the emulator runs on por `8085` on `localhost` and keep it running. Switch to a new terminal window,
set the pubsub environment variables and use the provided script to setup the pubsub topic and subscription:

```bash
$(gcloud beta emulators pubsub env-init)
./test-tools/pubsub_emulator_setup.sh
```

## Install and run the Comet example app

Open a third terminal window where you will install and run Comet:

Create and activate a virtual environment (run `sudo pip3 install virtualenv` first if you don't have 
Python `virtualenv` installed):

```bash
virtualenv -p `which python3.6` venv
source venv/bin/activate
```

Install the requirements:

```bash
pip install -r requirements.txt 
```

Set the pubusb environment variables, so that the pubsub input plugin will run correctly:

```bash
$(gcloud beta emulators pubsub env-init)
```

And run Comet:

```bash
python comet/main.py
```

Now you should see log messages reporting that Comet initialized, the last one saying:

> Starting the Comet app...

That means Comet is running and waiting for incoming alert messages :sparkles:

## Publish test messages

Open a fourth terminal window and use the provided script to feed one of the provided test alert messages to Comet
by publishing it to the pubsub topic:

```bash
$(gcloud beta emulators pubsub env-init)
./test-tools/pubsub_emulator_publish.sh forseti 
```

If you switch back to the terminal window where you have Comet running, you should see a new log message after some
seconds, saying that it would have sent an email about the alert that you just published.

You can run `./test-tools/pubsub_emulator_publish.sh` without any arguments to see the available test messages.

## Testing the API 

To test the API as well, you can open another terminal window, where you run the following commands to activate the 
virtual environment you created before and start the API. It will use the `comet-example.db` sqlite database file that
the Comet main application created. 

```bash
source venv/bin/activate
FLASK_APP=comet/api.py flask run
```

When you navigate to [localhost:5000/v0](http://localhost:5000/v0/) or run 
```bash
curl localhost:5000/v0/
```
you should see the success status message "Comet-API-v0". 

When you navigate to [localhost:5000/v0/issues](http://localhost:5000/v0/issues/) or run
```bash
curl localhost:5000/v0/issues
```
you should get the list of issues for the example user that you published through the pubsub emulator before.


To whitelist or snooze a specific alert by it's fingerprint, you can call the API routes responsible for this 
(`v0/falsepositive/`, `v0/acceptrisk/`, `v0/snooze/`), for example like this:
```bash
curl localhost:5000/v0/snooze \
  --header "Content-Type: application/json" \
  --request POST \
  --data '{"fingerprint": "FINGERPRINT_OF_ALERT_TO_SNOOZE"}'
```

# Plugins Writing 

To add a new alert source, first make sure that it can send messages to an existing input plugin or add a new input plugin for that purpose. For example, if the alert source can publish pubsub messages, you can use the the pubsub input plugin to receive these messages in Comet.

Then, you write a new Comet plugin that can handle these messages. This usually consists of these three to four steps:
write a parser, that is a schema that expresses what format the incoming message is expected to have, write a hydrator, that enriches incoming messages with additional data, such as looking up an owner for the resource that the alert is about, write a router that defines which output plugins should be used for messages from this alert source, and depending on which output plugins you choose, you might also want to write templates for them, for example a custom email template for email notifications.

## Example

Let’s assume you work in a company that has an office with several floors and that has a couple of toasters on each floor. Every toaster has a configurable default heat level and employees have the freedom to change that. You are working in the security team and you don’t want to block people from using high default heat levels, but you would at least like to warn them if they do so, to double check that this risky setting was actually intended. Luckily your company bought smart-toasters that can talk pubsub, so you configure the toasters to publish a pubsub message once per day in case a high default heat level was selected. As you are only a small security team, you cannot react on all of these alerts yourself, so you would like to distribute them to the “toaster owners” which are employees who are responsible for all the toasters on one floor (your identity management team has a database that is kept up to date with information about which employee is responsible for which floor). This is happens to be the perfect use-case for a distributed security alerting system like Comet, so let’s see how to use it to solve this task.

Let’s assume that the toasters send pubsub messages that have an attribute `source_type` set to “riskytoaster” (to distinguish it from other alert sources that might use pubsub as well) with a json blob in the data body that might look like this:

```json
{
    "toaster_id": "t7942",
    "toaster_location_floor": 1,
    "alert_type": "high-default-level",
    "comment": "Default level set to 7."
}
```

Now, let’s write the plugin:

### Parser

First, we define a marshmallow `Schema` that describes which fields we expect from the incoming message. In the example below, these are exactly the fields that we listed in the example alert message above. 

We assume that we have a Comet app instance assigned to the variable APP, so we call it’s `register_parser` method to register the schema as a parser for our source type.

```python
from marshmallow import fields, Schema

class RiskyToasterSchema(Schema):
    """Data Schema for risky toaster alarms."""
    toaster_id = fields.Str(required=True)
    toaster_location_floor = fields.Int(required=True)
    alert_type = fields.Str(required=True)
    comment = fields.Str(required=False)

APP.register_parser('riskytoaster', RiskyToasterSchema)
```

### Hydrator

Often, you want to enrich - or “hydrate” - the incoming messages with more data that is not directly provided by the alert source. In our example, there is a separate database for who is responsible for toasters on each floor - we call them toaster owners - and we assume that there is an API that we can access with the `find_toaster_owner` method that lets us look up the toaster owner given a floor number. So we want to write a hydrator that adds the ownership information to every incoming alert message using that API.

Assuming that you have a Comet app instance assigned to APP, you can register a hydrator for your alert source. You can do this by writing a function and decorating it with the `register_hydrator` method of the Comet app, which takes the source type that it can handle as an argument. In the example below, we call the toaster-owner API to assign an owner to an incoming event. We also populate a couple of metadata fields that can be used by output plugins or for generating metrics. For example, you want to aggregate the number of alerts per `resource` or organizational unit. For the latter, in the example code below, we assume that there is another API mapping email addresses to organizational units that can be accessed by the `get_organizational_unit` method.

```python
@APP.register_hydrator('riskytoaster')
def hydrate_riskytoaster(event):
    owner = find_toaster_owner(
event.message.get('toaster_location_floor'))

    event.set_owner(owner)

    event.set_metadata({
            'ou': get_organizational_unit(event.owner),
            'source_readable': 'Risky Toaster Alerting,
            'resource': event.message.get('toaster_id'),
            'resource_readable': f"Toaster {event.message.get('toaster_id')} on floor {event.message.get('toaster_location')}",
            'issue_type': event.message.get('alert_type'),
            'issue_type_readable': {'high-default-level': 'Toaster with high default level found.'
}.get(event.message.get('alert_type', 'Risky toaster found.')
})
```

### Router

Finally we need to make sure that risky toaster alerts are routed through the right channels to the toaster owners. A router is invoked every time there are new events for an alert source that need to be sent out. The router gets a list of events that are already grouped per owner, labelled as new or old (a `new` field is set to `True` or `False` depending on if an alert with the same fingerprint has been seen before) and where whitelisted and snoozed alerts are already filtered out.

In our example we assume that we have an EMAILER output plugin that can send emails, and simply deliver the list of events to the owner.

```python
@APP.register_router('riskytoaster')
def route (source_type, owner_email, events):
    EMAILER.send(recipient=owner_email,
subject='Risky toasters found',
template='risky_toaster_template.html', 
data=events)
```

In the email template `risky_toaster_template.html` we can do more grouping or sorting, assuming that one toaster owner is responsible for several toasters. For example alerts can be sorted by location or grouped by new/old status, first presenting all newly discovered risky toasters, and then having a reminder list about the still open issues for toasters that have been reported before but are not fixed yet.

### Filter

You can use our filter decorator as well, in cases you would want to filter messages by defined conditions before saving them into the DB.

In our example we assume that we have a filter function which includes filtering events only if their owner is one of our alpha customers, which we define in a different config file.

```python
@APP.register_filter('riskytoaster')
def filter(event):
   event_owner = event['owner']
   if event_owner in config.ALPHA_CUSTOMERS:
      return event
   return None
```

If the owner is not one of our alpha customers, we return None so that later the event won't be saved into the database.

# Code of Conduct

This project adheres to the [Open Code of Conduct][code-of-conduct]. By participating, you are expected to honor this code.

[code-of-conduct]: https://github.com/spotify/code-of-conduct/blob/master/code-of-conduct.md

