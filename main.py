# coding=utf-8

import requests
import json
import os
import os.path
import sys
import re
import datetime

slack_url = os.getenv('SLACK_URL')
if not slack_url:
    print('Provide a hook to your Slack workspace in the `SLACK_URL` environment property.\n(e.g. https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX)')
    sys.exit('Slack hook URL is necessary to post the overview into the workspace.')

approximate_citizen_count = 10_707_839

mzcr_url = 'https://onemocneni-aktualne.mzcr.cz/covid-19'

tests_url = 'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/testy-pcr-antigenni.json'
overview_url = 'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/zakladni-prehled.json'
vaccinations_url = 'https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani.json'

tests_json = requests.get(tests_url).json()
overview_json = requests.get(overview_url).json()
vaccinations_json = requests.get(vaccinations_url).json()

# TODO: Post detailed info about vaccine distribution and tests with and without symptoms into message's thread.
tests_pcr = sum(int(data_point['pocet_PCR_testy']) for data_point in tests_json['data'])
tests_antigen = sum(int(data_point['pocet_AG_testy']) for data_point in tests_json['data'])

vaccines_by_name = { data_point['vakcina'] for data_point in vaccinations_json['data'] }
total_first_dose_vaccinations = sum(int(data_point['prvnich_davek']) for data_point in vaccinations_json['data'])
total_first_dose_vaccinations_percentage = '{:.1%}'.format(total_first_dose_vaccinations / approximate_citizen_count)
total_second_dose_vaccinations = sum(int(data_point['druhych_davek']) for data_point in vaccinations_json['data'])
total_second_dose_vaccinations_percentage = '{:.1%}'.format(total_second_dose_vaccinations / approximate_citizen_count)

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
        ('total_infections', overview_json['data'][0]['potvrzene_pripady_celkem']),
        ('active_infections', overview_json['data'][0]['aktivni_pripady']),
        ('recoveries', overview_json['data'][0]['vyleceni']),
        ('hospitalized', overview_json['data'][0]['aktualne_hospitalizovani']),
        ('deceased', overview_json['data'][0]['umrti']),
        ('vaccinations_first_dose', total_first_dose_vaccinations),
        ('vaccinations_second_dose', total_second_dose_vaccinations),
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

def format_modified(date):
    return date.strftime("%d/%m/%Y @ %H:%M")

def modified(data):
    return datetime.datetime.strptime(data['modified'], '%Y-%m-%dT%H:%M:%S%z')

tests_modified = modified(tests_json)
overview_modified = modified(overview_json)
vaccinations_modified = modified(vaccinations_json)

previous_total_tests = None

previous_pcr_tests = previous_data.get('tests_pcr')
if previous_pcr_tests is not None:
    previous_total_tests = (previous_total_tests or 0) + previous_pcr_tests

previous_antigen_tests = previous_data.get('tests_antigen')
if previous_antigen_tests is not None:
    previous_total_tests = (previous_total_tests or 0) + previous_antigen_tests

class Slack:
    def section(text):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }

    def context(text):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": text
                }
            ]
        }

    def header(text):
        return {
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": text,
				"emoji": True
			}
		}

    def spacer():
        return {
			"type": "section",
			"text": {
				"type": "plain_text",
				"text": " ",
				"emoji": False
			}
		}

    def divider():
        return { "type": "divider" }

    def overflow(text, elements):
        return {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": text
			},
			"accessory": {
				"type": "overflow",
				"options": [
					map(overflow_item, elements)
				]
			}
		}

    def overflow_item(text):
        return {
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            }
        }


payload = {
    "blocks": [
		Slack.header("Situace – {}".format(datetime.datetime.now().strftime("%d/%m/%Y"))),
        Slack.section(
            "[Tests] :female-doctor: :male-doctor:" +
            "\n\t PCR: *{}*{}".format(
                format_number(current_data['tests_pcr']),
                format_comparison(previous_data.get('tests_pcr'), current_data['tests_pcr']),
            ) +
            "\n\t Antigen: *{}*{}".format(
                format_number(current_data['tests_antigen']),
                format_comparison(previous_data.get('tests_antigen'), current_data['tests_antigen']),
            ) +
            "\n\t Total: *{}*{}".format(
                format_number(current_data['tests_pcr'] + current_data['tests_antigen']),
                format_comparison(previous_total_tests, current_data['tests_pcr'] + current_data['tests_antigen']),
            )
        ),
        Slack.context("Last update: *{}*".format(format_modified(tests_modified))),
        Slack.divider(),
        Slack.section(
            "[Infections] :zombie: :female_zombie:" +
            "\n\t Active: *{}*{}".format(
                format_number(current_data['active_infections']),
                format_comparison(previous_data.get('active_infections'), current_data['active_infections']),
            ) +
            "\n\t Recovered: *{}*{}".format(
                format_number(current_data['recoveries']),
                format_comparison(previous_data.get('recoveries'), current_data['recoveries']),
            ) +
            "\n\t Total: *{}*{}".format(
                format_number(current_data['total_infections']),
                format_comparison(previous_data.get('total_infections'), current_data['total_infections']),
            )
        ),
        Slack.context("Last update: *{}*".format(format_modified(overview_modified))),
        Slack.divider(),
        Slack.section(
            "[Losses] :hospital: :f:" +
            "\n\t Hospitalized: *{}*{}".format(
                format_number(current_data['hospitalized']),
                format_comparison(previous_data.get('hospitalized'), current_data['hospitalized']),
            ) +
            "\n\t Deceased: *{}*{}".format(
                format_number(current_data['deceased']),
                format_comparison(previous_data.get('deceased'), current_data['deceased']),
            )
        ),
        Slack.context("Last update: *{}*".format(format_modified(overview_modified))),
        Slack.divider(),
        Slack.section(
            "[Vaccinations] :syringe: :pill:" +
            "\n\t First dose: *{}* ≅ {}{}".format(
                format_number(current_data['vaccinations_first_dose']),
                total_first_dose_vaccinations_percentage,
                format_comparison(previous_data.get('vaccinations_first_dose'), current_data['vaccinations_first_dose']),
            ) +
            "\n\t Second dose: *{}* ≅ {}{}".format(
                format_number(current_data['vaccinations_second_dose']),
                total_second_dose_vaccinations_percentage,
                format_comparison(previous_data.get('vaccinations_second_dose'), current_data['vaccinations_second_dose']),
            )
        ),
        Slack.context("Last update: *{}*".format(format_modified(vaccinations_modified))),
        Slack.divider(),
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*For more info click this button:*"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "MZČR",
                    "emoji": True
                },
                "url": mzcr_url
            }
        }
    ]
}

requests.post(slack_url, json=payload)
