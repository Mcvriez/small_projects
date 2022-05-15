from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging


def send(cfg, text='', blocks=None):
    if blocks is None:
        blocks = []
    client = WebClient(token=cfg.slack_token)
    try:
        response = client.chat_postMessage(
            channel=cfg.slack_channel,
            link_names=1,
            text=text,
            blocks=blocks)
    except SlackApiError as e:
        logging.error(f"Got an error: {e.response['error']}")


def send_file(symbol, cfg, file_path, ftype='png'):
    client = WebClient(token=cfg.slack_token)
    try:
        with open(file_path, "rb"):
            response = client.files_upload(
                channels=cfg.slack_channel,
                file=file_path,
                title=f'{symbol}.png',
                filetype=ftype
            )
            return response
    except SlackApiError as e:
        logging.error(f"message: {e.message}, response: {e.response}")
