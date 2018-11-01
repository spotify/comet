#!/usr/bin/env bash
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

PROJECT_ID=comet-example-project
PUBSUB_TOPIC=comet-example-topic
PUBSUB_SUBSCRIPTION=comet-example-subscription
PUBSUB_HOST=http://127.0.0.1:8085

curl -H 'Content-Type: application/json' -X PUT  -d '{}' "${PUBSUB_HOST}/v1/projects/${PROJECT_ID}/topics/${PUBSUB_TOPIC}"
curl -H 'Content-Type: application/json' -X PUT  -d "{\"topic\":\"projects/${PROJECT_ID}/topics/${PUBSUB_TOPIC}\"}" "${PUBSUB_HOST}/v1/projects/${PROJECT_ID}/subscriptions/${PUBSUB_SUBSCRIPTION}"
