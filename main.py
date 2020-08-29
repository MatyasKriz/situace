# coding=utf-8

import requests
import json
from bs4 import BeautifulSoup
import os
import os.path
import sys
import re

slack_url = os.getenv('SLACK_URL')
if not slack_url:
    print('Provide a hook to your Slack workspace in the `SLACK_URL` environment property.\n(e.g. https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX)')
    sys.exit('Slack hook URL is necessary to post the overview into the workspace.')

mzcr_url = 'https://onemocneni-aktualne.mzcr.cz/covid-19'

page = requests.get(mzcr_url)
soup = BeautifulSoup(page.content, 'html.parser')

def updated(count):
    regex = re.compile('k datu:(.*?)h')
    text = count.parent.parent.findChildren('p', recursive=False)[-1].text.strip()
    date = regex.search(text).group(1)
    return date.replace("v", "@").strip()

tested = soup.find(id='count-test')
tested_updated = updated(tested.parent)
infected = soup.find(id='count-sick')
infected_updated = updated(infected.parent.parent)
active = soup.find(id='count-active')
active_updated = updated(active.parent)
recovered = soup.find(id='count-recover')
recovered_updated = updated(recovered)
dead = soup.find(id='count-dead')
dead_updated = updated(dead)

# We're rewriting that file. If it's not ours, it has no business being here.
if not os.path.isfile('previous.json'):
    open('previous.json', 'w').close()

with open('previous.json', 'r+') as f:
    previous_data = f.read()
    current_data_points = [
        ('tested', tested),
        ('total_infected', infected),
        ('infected', active),
        ('recovered', recovered),
        ('dead', dead),
    ]
    current_data = {key: int(''.join(value.string.split())) for key, value in current_data_points}
    f.seek(0)
    f.write(json.dumps(current_data, indent=2))
    f.truncate()

if previous_data:
    previous_data = json.loads(previous_data)
    def comparison(value):
        if value == 0:
            return 'unchanged'

        return '{}{}'.format(
            '+' if value > 0 else '',
            value
        )
    comparisons = {key: ' ({})'.format(comparison(current_data[key] - previous_data[key])) for key in previous_data}
else:
    comparisons = {key: '' for key in current_data}

payload = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":female-doctor:  *{}* tested{}  :male-doctor:".format(tested.string, comparisons['tested'])
    	    }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Last update: *{}*".format(tested_updated)
                }
            ]
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bar_chart:  *{}* infected total{}  :chart_with_upwards_trend:".format(infected.string, comparisons['total_infected'])
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Last update: *{}*".format(infected_updated)
                }
            ]
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":zombie:  *{}* currently infected{}  :female_zombie:".format(active.string, comparisons['infected'])
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Last update: *{}*".format(active_updated)
                }
            ]
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":woman-tipping-hand:  *{}* recovered{}  :man-tipping-hand:".format(recovered.string, comparisons['recovered'])
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Last update: *{}*".format(recovered_updated)
                }
            ]
        },
        { "type": "divider" },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":skull:  *{}* dead{}  :skull:".format(dead.string, comparisons['dead'])
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Last update: *{}*".format(dead_updated)
                }
            ]
        },
        { "type": "divider" },
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
