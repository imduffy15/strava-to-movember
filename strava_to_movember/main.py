import click
from clickclick import Action, choice, error, AliasedGroup, info, print_table, OutputFormat
import os
from pathlib import Path
import keyring
from strava_to_movember.utils import yamlify
import yaml
import requests
import time
from strava_to_movember import __version__
import dateutil.parser as dp
import json

MODULE_NAME = __name__.split('.')[0]
CONFIG_DIR_PATH = click.get_app_dir(MODULE_NAME)
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, 'config.yaml')

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'{MODULE_NAME} {__version__}')
    ctx.exit()


@click.group()
@click.option('--config-file',
              '-c',
              help='Use alternative configuration file',
              default=CONFIG_FILE_PATH)
@click.option('-V',
              '--version',
              is_flag=True,
              callback=print_version,
              expose_value=False,
              is_eager=True,
              help='Print the current version number and exit.')
@click.pass_context
def main(ctx: click.core.Context, config_file: str):
    path = Path(config_file)
    data = {}

    if path.exists() and path.is_file():
        with open(config_file, 'rb') as fd:
            data = yaml.safe_load(fd)
    ctx.obj = {'config': data, 'config_file': path, 'config_dir': path.parent}


@main.command()
@click.argument('profile_name', nargs=-1)
@click.option("--strava-token",
              prompt="authentication token for accessing strava",
              envvar="STRAVA_AUTH_TOKEN")
@click.pass_obj
def sync(obj, profile_name, strava_token):
    if not profile_name:
        profile_name = obj['config']['default_profile']

    if profile_name not in obj['config']["profiles"]:
        raise click.ClickException(
            f"{profile_name} doesn't exist, please run \"strava_to_movember configure\""
        )

    if 'movember_email' not in obj['config']["profiles"][profile_name]:
        raise click.ClickException(
            'Missing Movember email. please run "strava_to_movember configure"'
        )
    movember_email = obj['config']["profiles"][profile_name]['movember_email']
    movember_password = keyring.get_password(f"{MODULE_NAME}_{profile_name}",
                                             "movember_password")
    if not movember_password:
        raise click.ClickException(
            'Missing Movember password. please run "strava_to_movember configure"'
        )

    movember_authentication_details = authenticate_movember(
        movember_email, movember_password)

    strava_data = get_strava_data(strava_auth_token=strava_token)

    for move in strava_data:
        # print(json.dumps(move, indent=4))
        create_movember_move(
            auth_token=movember_authentication_details["accessToken"],
            member_id=movember_authentication_details["memberId"],
            **move)


def get_strava_data(strava_auth_token,
                    after="1572566400",
                    per_page=30,
                    page=1,
                    data=[]):
    req = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}&page={page}&after={after}",
        headers={"Authorization": f"Bearer {strava_auth_token}"})

    payload = req.json()

    for item in payload:
        data.append({
            "distance":
            item["distance"],
            "distance_unit":
            "kilometres",
            "duration":
            item["moving_time"],
            "start_date":
            int(dp.parse(item["start_date"]).strftime('%s')),
            "move_type":
            1 if item["type"] == "Walk" else 2
        })

    if len(payload) > 0:
        page = page + 1
        return get_strava_data(strava_auth_token, after, per_page, page, data)
    else:
        return data


def create_movember_move(auth_token, member_id, distance, distance_unit,
                         duration, start_date, move_type):
    req = requests.post("https://api.movember.com/v18/newsfeed/",
                        headers={
                            "x-member-auth-token": auth_token,
                            "x-member-auth-id": member_id
                        },
                        json={
                            "authorId": member_id,
                            "authorType": "member",
                            "content": "\n",
                            "entityId": member_id,
                            "entityType": "member",
                            "moveData": {
                                "distance": distance,
                                "distance_unit": distance_unit,
                                "duration": duration,
                                "moveDate": start_date,
                                "moveTypeId": move_type
                            }
                        })
    return req.json()


def authenticate_movember(movember_email, movember_password):
    req = requests.post("https://api.movember.com/v18/auth/",
                        json={
                            "username": movember_email,
                            "password": movember_password
                        })
    return req.json()


@main.command()
@click.option("--movember-email",
              prompt="email for accessing Movember",
              envvar="MOVEMBER_EMAIL")
@click.option("--movember-password",
              prompt="Password for accessing Movember",
              hide_input=True,
              envvar="MOVEMBER_PASSWORD")
@click.pass_obj
def configure(obj, movember_email: str, movember_password: str):
    data = obj['config']
    if not data:
        data = {'default_profile': "default", 'profiles': {}}

    data['profiles']["default"] = {"movember_email": movember_email}
    keyring.set_password(f"{MODULE_NAME}_default", "movember_password",
                         movember_password)

    path = Path(obj['config_dir'])
    with Action(f'Storing configuration in {obj["config_file"]}'):
        path.mkdir(exist_ok=True, parents=True)
        with open(obj['config_file'], 'w') as fd:
            fd.write(yamlify(data))
