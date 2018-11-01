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

SCRIPT_PATH="$( cd "$(dirname "$0")" ; pwd -P )"
TEST_DATA_DIR=${SCRIPT_PATH}/../test-alerts


# Unset on both exit and ctrl+c
function cleanup {
    gcloud config unset api_endpoint_overrides/pubsub 2> /dev/null
}
trap cleanup EXIT

gcloud config set api_endpoint_overrides/pubsub http://localhost:8085/ 2> /dev/null

if [ $# != 1 ] || [ ! -f "${TEST_DATA_DIR}/$1.message" ] ; then
    echo "Run using ./pubsub_emulate_publish.sh <data-source>"
    echo
    echo "Valid data sources:"
    for entry in ${TEST_DATA_DIR}/*
    do
        filename=$(basename "$entry")
        echo " * ${filename%.*}"
    done
    exit 1;
fi

gcloud pubsub topics publish ${PUBSUB_TOPIC} --project ${PROJECT_ID} --message "`cat ${TEST_DATA_DIR}/$1.message`" --attribute="source_type=${1%%.*}" > /dev/null

echo "Successfully published a $1 message"
