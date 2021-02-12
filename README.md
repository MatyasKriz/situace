# Situace
This is a simple Python script that fetches MZČR JSON info about the coronasituace in Czechia and posts it to Slack workspace.

![](./res/screenshot.png)

### Usage
- Clone the repo somewhere and `cd` into it.
- Create a virtual environment using `venv`.
```
python3 -m venv env
```
- Install dependencies.
```
env/bin/pip install -r requirements.txt
```

#### Regular Updates
I've found that the easiest way to run this script regularly is through crontab.

**IMPORTANT**: On MacOS your terminal application needs to have "Full Disk Access" permission (in Security and Privacy) to write data into `previous.json` so that the next run can calculate differences.

To edit your crontab, simply run
```
crontab -e
```

This should open the crontab file with some editor,
paste this at the end of it:
```
SLACK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
0 18 * * * cd PATH_TO_REPO && env/bin/python main.py
```

- Replace `PATH_TO_REPO` with the path to the cloned repository.
- Replace the `SLACK_URL` value with a Slack webhook for your workspace.
- Consult [crontab.guru](https://crontab.guru/) for customizing times of execution, this combination fires every day at 6 PM (18:00).

### License
**MIT**, more in the `LICENSE` file.
