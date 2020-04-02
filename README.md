# Situace
This is a simple Python script that scrapes MZČR info about the coronasituace in Czechia and posts it to Slack workspace.

### Usage
- Clone the repo somewhere and copy the path.
- [pipenv](https://packaging.python.org/tutorials/managing-dependencies/) is used for managing the dependencies for this script. (BeautifulSoup & Requests)
- If you have `pipenv` installed, simply `cd` into the cloned directory and run
```
pipenv run python main.py
```

#### Regular Updates
I've found that the easiest way to run this script regularly is through crontab.

**IMPORTANT**: On MacOS your terminal application needs to have "Full Disk Access" permission (Security and Privacy).

To edit your crontab, simply run
```
crontab -e
```

This should open the crontab file with some editor,
paste this at the end of it:
```
SHELL=/bin/bash
SLACK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
0 18 * * * cd PATH_TO_REPO && /usr/local/bin/pipenv run python main.py
```

- Replace `PATH_TO_REPO` with the path to the cloned repository.
- Replace the `SLACK_URL` value with a Slack webhook for your workspace.
- Consult [crontab.guru](https://crontab.guru/) for customizing times of execution, this combination fires every day at 6 PM (18:00).

### License
**MIT**, more in the `LICENSE` file.
