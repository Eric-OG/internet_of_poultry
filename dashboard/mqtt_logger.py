from typing import Dict, List
from datetime import datetime

from dash import html


class MqttLogger:
    _logs: List[html.P]
    _has_been_updated: bool

    def __init__(self):
        self._logs = []
        self._has_been_updated = False

    def log_message(self, msg: Dict, topic: str):
        topic_str = topic.split('/', 1)[1]
        origin, endpoint = topic_str.split('/', 1)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header_str = topic_str + (':' if msg is not None else '')
        msg_str =  str(msg) if msg is not None else ''
        sep_str = html.Br() if msg is not None else None

        style = {'border': "1px solid", "border-color": "rgba(87, 87, 87, 0.2)"}
        className = "m-0 p-2 fs-5 text-wrap"
        match origin:
            case "dash":
                style["background-color"] = "rgba(101, 168, 209, 0.8)"
            case "mesh":
                style["background-color"] = "rgba(90, 204, 139, 0.8)"

        text_content = [html.B(timestamp), "    ", header_str, sep_str, msg_str]
        self._logs.append(html.Pre(text_content, className=className, style=style))
        self._has_been_updated = True

    def get_logs(self) -> List[html.P]:
        self._has_been_updated = False
        return self._logs

    @property
    def has_been_updated(self):
        return self._has_been_updated
