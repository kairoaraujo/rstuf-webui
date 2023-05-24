# SPDX-FileCopyrightText: 2022-2023 VMware Inc
#
# SPDX-License-Identifier: MIT
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

import requests
from dynaconf import LazySettings
from requests.exceptions import ConnectionError



class URL(Enum):
    token = "api/v1/token/"  # nosec bandit: not hard coded password.
    bootstrap = "api/v1/bootstrap/"
    task = "api/v1/task/?task_id="
    publish_targets = "api/v1/targets/publish/"
    metadata_signing = "api/v1/metadata/sign/"


class Methods(Enum):
    get = "get"
    post = "post"


@dataclass
class Login:
    state: bool
    data: Optional[Dict[str, Any]] = None


def request_server(
    server: str,
    url: str,
    method: Methods,
    payload: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    if method == Methods.get:
        response = requests.get(
            f"{server}/{url}", json=payload, data=data, headers=headers
        )

    elif method == Methods.post:
        response = requests.post(
            f"{server}/{url}", json=payload, data=data, headers=headers
        )

    else:
        raise ValueError("Internal Error. Invalid HTTP/S Method.")

    return response


def is_logged(settings: LazySettings, token: Optional[Dict[str, str]] = None):
    if token is None:
        return Login(state=False)

    server = settings.get("SERVER")
    headers = token

    url = f"{URL.token.value}?token={token}"
    response = request_server(server, url, Methods.get, headers=headers)
    if response.status_code == 401 or response.status_code == 403:
        return Login(state=False)

    elif response.status_code == 200:
        data = response.json().get("data", {})
        if data.get("expired") is False:
            return Login(state=True, data=data)

    else:
        return Login(state=False)

@dataclass
class BootstapStatus:
    status: bool
    message: str

def bootstrap_status(settings: LazySettings, cookie: Dict[str, str]) -> BootstapStatus:
    print(cookie)
    response = request_server(
        settings.SERVER, URL.bootstrap.value, Methods.get, headers=cookie
    )
    if response.status_code == 404:
        return BootstapStatus(False, f"Server {settings.SERVER} does not allow bootstrap")

    bootstrap_json = response.json()
    print(bootstrap_json)
    status = bootstrap_json["data"]["bootstrap"]
    message = bootstrap_json["message"]
    return BootstapStatus(status, message)


def task_status(
    task_id: str,
    settings: LazySettings,
) -> Dict[str, Any]:
    headers = get_headers(settings)
    received_states = []
    while True:
        state_response = request_server(
            settings.SERVER,
            f"{URL.task.value}{task_id}",
            Methods.get,
            headers=headers,
        )

        if state_response.status_code != 200:
            raise ConnectionError(
                f"Unexpected response {state_response.text}"
            )

        data = state_response.json().get("data")

        if data:
            if state := data.get("state"):
                if state not in received_states:
                    received_states.append(state)

                if state == "SUCCESS":
                    return data

                elif state == "FAILURE":
                    raise ConnectionError(
                        f"Failed: {state_response.text}"
                    )

            else:
                raise ConnectionError(
                    f"No state in data received {state_response.text}"
                )
        else:
            raise ConnectionError(
                f"No data received {state_response.text}"
            )
        time.sleep(2)


def publish_targets(settings: LazySettings) -> str:
    headers = get_headers(settings)
    publish_targets = request_server(
        settings.SERVER,
        URL.publish_targets.value,
        Methods.post,
        headers=headers,
    )
    if publish_targets.status_code != 202:
        raise ConnectionError(
            f"Failed to publish targets. {publish_targets.status_code} "
            f"{publish_targets.text}"
        )
    task_id = publish_targets.json()["data"]["task_id"]

    return task_id

def auth_enabled(settings: LazySettings):
    auth_response = request_server(
        settings.SERVER, URL.token.value, Methods.get
    )
    if auth_response.status_code == 404:
        return False
    else:
        return True