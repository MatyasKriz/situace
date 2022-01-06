# coding=utf-8

import requests
import json
import os
import sys
import re
import datetime
import csv

space_url = os.getenv('SPACE_URL')
if not space_url:
    print('Provide a JetBrains Space URL in the `SPACE_URL` environment property.')
    sys.exit('JetBrains Space URL is necessary to post the overview into the workspace.')

space_access_token = os.getenv('SPACE_ACCESS_TOKEN')
if not space_access_token:
    print('Provide a JetBrains Space Access Token in the `SPACE_ACCESS_TOKEN` environment property.')
    sys.exit('JetBrains Space Access Token is necessary to post the overview into the workspace.')

space_channel_id = os.getenv('SPACE_CHANNEL_ID')
if not space_channel_id:
    print('Provide a JetBrains Space Channel ID in the `SPACE_CHANNEL_ID` environment property.')
    sys.exit('JetBrains Space Channel ID is necessary to post the overview into the workspace.')

mzcr_url = 'https://onemocneni-aktualne.mzcr.cz/covid-19'

overview_url = 'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.csv'

overview_csv = next(csv.DictReader(requests.get(overview_url).content.decode('utf-8-sig').splitlines()))

tests_antigen = overview_csv['provedene_antigenni_testy_celkem']
tests_pcr = int(overview_csv['provedene_testy_celkem'])

total_vaccinations = int(overview_csv['vykazana_ockovani_celkem'])

# We're rewriting that file. If it's not ours, it has no business being here.
dirname = os.path.dirname(__file__)
previous_data_path = os.path.join(dirname, 'previous.json')
if not os.path.isfile(previous_data_path):
    open(previous_data_path, 'w').close()

with open(previous_data_path, 'r+') as f:
    previous_data = f.read()
    current_data_points = [
        ('tests_pcr', tests_pcr),
        ('tests_antigen', tests_antigen),
        ('total_infections', overview_csv['potvrzene_pripady_celkem']),
        ('active_infections', overview_csv['aktivni_pripady']),
        ('recoveries', overview_csv['vyleceni']),
        ('hospitalized', overview_csv['aktualne_hospitalizovani']),
        ('deceased', overview_csv['umrti']),
        ('total_vaccinations', total_vaccinations),
    ]
    current_data = {key: int(value) for key, value in current_data_points}
    f.seek(0)
    f.write(json.dumps(current_data, indent=2))
    f.truncate()

if previous_data:
    previous_data = json.loads(previous_data)
else:
    previous_data = {}


def format_number(number):
    return f'{number:,}'.replace(',', ' ').strip()

def format_comparison(old_value, new_value):
    if old_value is not None:
        comparison = new_value - old_value
        if comparison == 0:
            return ' (unchanged)'

        return ' ({}{})'.format(
            '+' if comparison > 0 else '',
            format_number(comparison)
        )
    else:
        return ''

previous_total_tests = None

previous_pcr_tests = previous_data.get('tests_pcr')
if previous_pcr_tests is not None:
    previous_total_tests = (previous_total_tests or 0) + previous_pcr_tests

previous_antigen_tests = previous_data.get('tests_antigen')
if previous_antigen_tests is not None:
    previous_total_tests = (previous_total_tests or 0) + previous_antigen_tests

class Space:
    def header(text):
        return {
            "className": "MessageSection",
            "header": text,
            "elements": []
        }


    def section(text):
        return {
            "className": "MessageSection",
            "elements": [{
                "className": "MessageText",
                "content": text
            }]
        }

    def divider():
        return { "className": "MessageDivider" }


payload = {
    "recipient": "channel:id:{}".format(space_channel_id),
    "content": {
        "className": "ChatMessage.Block",
        "sections": [
            Space.header("Situace – {}".format(datetime.datetime.now().strftime("%d/%m/%Y"))),
            Space.section(
                "[Tests] 👩‍⚕️ 👨‍⚕️" +
                "\n• PCR: **{}**{}".format(
                    format_number(current_data['tests_pcr']),
                    format_comparison(previous_data.get('tests_pcr'), current_data['tests_pcr']),
                ) +
                "\n• Antigen: **{}**{}".format(
                    format_number(current_data['tests_antigen']),
                    format_comparison(previous_data.get('tests_antigen'), current_data['tests_antigen']),
                ) +
                "\n• Total: **{}**{}".format(
                    format_number(current_data['tests_pcr'] + current_data['tests_antigen']),
                    format_comparison(previous_total_tests, current_data['tests_pcr'] + current_data['tests_antigen']),
                )
            ),
            Space.divider(),
            Space.section(
                "[Infections] 🧟 🧟‍♀️" +
                "\n• Active: **{}**{}".format(
                    format_number(current_data['active_infections']),
                    format_comparison(previous_data.get('active_infections'), current_data['active_infections']),
                ) +
                "\n• Recovered: **{}**{}".format(
                    format_number(current_data['recoveries']),
                    format_comparison(previous_data.get('recoveries'), current_data['recoveries']),
                ) +
                "\n• Total: **{}**{}".format(
                    format_number(current_data['total_infections']),
                    format_comparison(previous_data.get('total_infections'), current_data['total_infections']),
                )
            ),
            Space.divider(),
            Space.section(
                "[Losses] 🏥 🪦" +
                "\n• Hospitalized: **{}**{}".format(
                    format_number(current_data['hospitalized']),
                    format_comparison(previous_data.get('hospitalized'), current_data['hospitalized']),
                ) +
                "\n• Deceased: **{}**{}".format(
                    format_number(current_data['deceased']),
                    format_comparison(previous_data.get('deceased'), current_data['deceased']),
                )
            ),
            Space.divider(),
            Space.section(
                "[Vaccinations] 💉 💊" +
                "\n• Doses administered: **{}**{}".format(
                    format_number(current_data['total_vaccinations']),
                    format_comparison(previous_data.get('total_vaccinations'), current_data['total_vaccinations']),
                )
            ),
            Space.divider(),
            {
            "className": "MessageSection",
            "elements": [
            {
              "className": "MessageText",
              "accessory": {
                "className": "MessageIcon",
                "icon": {
                  "icon": "info-small"
                },
                "style": "SECONDARY"
              },
              "content": "For more info click this button:"
            },
            {
                "className": "MessageControlGroup",
                "elements": [
                  {
                    "className": "MessageButton",
                    "text": "MZČR",
                    "style": "REGULAR",
                    "action": {
                      "className": "NavigateUrlAction",
                      "url": mzcr_url,
                      "withBackUrl": False,
                      "openInNewTab": True
                    }
                  }
                ]
            }
            ],
            "footer": "Stay safe!"
          }
        ]
    }
}

headers = {
    'Authorization': 'Bearer {}'.format(space_access_token),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

requests.post(space_url, headers=headers, json=payload)
