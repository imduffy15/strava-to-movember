# Strava to Movember

Syncs Strava data to Movember

## Getting Started

Install appliation dependencies:

```
$ pip install pipenv
$ pipenv install
```

Run application:

```
$ pipenv run python -m strava_to_movember
```

## Usage

Generate a token to authenticate with strava, this can be done using https://github.com/imduffy15/token-cli :

```
$ token-cli target create strava --token-url https://www.strava.com/oauth/token --authorizaion-url http://www.strava.com/oauth/authorize
$ token-cli target set strava
$ export STRAVA_AUTH_TOKEN=$(token-cli token get 40638 --client_secret e36b1089bfe26c8010cd10eabe419c96493c412b --scope activity:read_all)
```

Configure strava-to-movember :

```
$ pipenv run python -m strava_to_movember configure
email for accessing Movember: email@domain.com
Password for accessing Movember: 
Storing configuration in /Users/duffy/Library/Application Support/strava_to_movember/config.yaml OK
```

Syncing strava to movember:

```
$ pipenv run python -m strava_to_movember sync
```
