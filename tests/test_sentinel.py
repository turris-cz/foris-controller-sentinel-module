#
# foris-controller-sentinel-module
# Copyright (C) 2019-2023 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#

import pytest
import textwrap

from .conftest import CMDLINE_SCRIPT_ROOT

from foris_controller_testtools.fixtures import UCI_CONFIG_DIR_PATH
from foris_controller_testtools.utils import (
    get_uci_module,
    command_was_called,
    FileFaker
)


@pytest.fixture(scope="function")
def sentinel_status(request):
    content = """\
        #!/bin/sh
        echo "FWLogs: {}"
        echo "Minipot: {}"
        echo "Turris Survey: {}"
        echo "Server Connection: {}"
    """
    if hasattr(request, "param"):
        content = content.format(*request.param)
        with FileFaker(CMDLINE_SCRIPT_ROOT, "/usr/bin/sentinel-status", True, textwrap.dedent(content)) as f:
            yield f


@pytest.fixture(scope="function")
def sentinel_status_malformed_data(request):
    """ Mock malformed sentinel status output """
    content = """\
        #!/bin/sh
        echo "foo-logs: F/O/O"
        echo " Minipot: b<a>r"
        echo "  Turris Qu=ux"
        echo ": Something-Completely_Broken"
    """
    with FileFaker(CMDLINE_SCRIPT_ROOT, "/usr/bin/sentinel-status", True, textwrap.dedent(content)) as f:
        yield f


@pytest.mark.parametrize('device,turris_os_version', [("mox", "4.0")], indirect=True)
def test_get_settings(updater_userlists, updater_languages, file_root_init, infrastructure, uci_configs_init, device, turris_os_version):
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert "error" not in res
    assert "data" in res
    assert "eula" in res["data"]
    assert "token" in res["data"]
    assert {"minipot", "fwlogs", "survey"} == res["data"]["modules"].keys()
    assert {"ftp", "http", "smtp", "telnet"} == res["data"]["modules"]["minipot"]["protocols"].keys()


def test_update_settings(
    file_root_init, infrastructure, init_script_result, uci_configs_init, updater_userlists, updater_languages
):
    filters = [("sentinel", "update_settings")]

    # once eula is set to be < 0 a token should be generated
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {"eula": 1}}
    )
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "sentinel",
        "action": "update_settings",
        "kind": "notification",
        "data": {"eula": 1},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["eula"] == 1
    assert res["data"]["token"] is not None
    original_token = res["data"]["token"]

    # once eula is set to 0 and orig token is returned
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {"eula": 0}}
    )
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "sentinel",
        "action": "update_settings",
        "kind": "notification",
        "data": {"eula": 0},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["eula"] == 0
    assert res["data"]["token"] == original_token

    # set custom token
    token = "a" * 64
    res = infrastructure.process_message(
        {
            "module": "sentinel",
            "action": "update_settings",
            "kind": "request",
            "data": {"eula": 1, "token": token},
        }
    )
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "sentinel",
        "action": "update_settings",
        "kind": "notification",
        "data": {"eula": 1},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["eula"] == 1
    assert res["data"]["token"] == token


@pytest.mark.only_backends(["openwrt"])
def test_update_settings_openwrt(
    updater_userlists, updater_languages, file_root_init, infrastructure, init_script_result, uci_configs_init
):
    uci = get_uci_module(infrastructure.name)

    # once eula is set to be < 0 a token should be generated
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {"eula": 1}}
    )
    assert command_was_called(["sentinel-reload"])

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    original_token = res["data"]["token"]

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as uci_backend:
        data = uci_backend.read()
    assert int(uci.get_option_named(data, "sentinel", "main", "agreed_with_eula_version")) == 1
    assert uci.get_option_named(data, "sentinel", "main", "device_token") == original_token

    # set custom token
    token = "a" * 64
    res = infrastructure.process_message(
        {
            "module": "sentinel",
            "action": "update_settings",
            "kind": "request",
            "data": {"eula": 2, "token": token},
        }
    )
    assert command_was_called(["sentinel-reload"])

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as uci_backend:
        data = uci_backend.read()
    assert int(uci.get_option_named(data, "sentinel", "main", "agreed_with_eula_version")) == 2
    assert uci.get_option_named(data, "sentinel", "main", "device_token") == token


def test_get_fakepot_settings(file_root_init, infrastructure, uci_configs_init):
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_fakepot_settings", "kind": "request"}
    )
    assert "error" not in res
    assert "data" in res
    assert "enabled" in res["data"]
    assert "extra_option" in res["data"]


def test_update_fakepot_settings(
    file_root_init, infrastructure, init_script_result, uci_configs_init
):
    filters = [("sentinel", "update_fakepot_settings")]

    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {
            "module": "sentinel",
            "action": "update_fakepot_settings",
            "kind": "request",
            "data": {"enabled": True, "extra_option": "first"},
        }
    )
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        "module": "sentinel",
        "action": "update_fakepot_settings",
        "kind": "notification",
        "data": {"enabled": True, "extra_option": "first"},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_fakepot_settings", "kind": "request"}
    )
    assert res["data"]["enabled"]
    assert res["data"]["extra_option"] == "first"


@pytest.mark.only_backends(["openwrt"])
def test_update_fakepot_settings_openwrt(
    file_root_init, infrastructure, init_script_result, uci_configs_init
):
    uci = get_uci_module(infrastructure.name)

    infrastructure.process_message(
        {
            "module": "sentinel",
            "action": "update_fakepot_settings",
            "kind": "request",
            "data": {"enabled": True, "extra_option": "second"},
        }
    )

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as uci_backend:
        data = uci_backend.read()

    assert uci.parse_bool(uci.get_option_named(data, "sentinel", "fakepot", "enabled"))
    assert uci.get_option_named(data, "sentinel", "fakepot", "extra_option") == "second"


def test_update_settings_invalid_eula(
    updater_userlists, updater_languages, file_root_init, infrastructure, init_script_result, uci_configs_init
):

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    prev_eula = res["data"]["eula"]

    token = "b" * 64
    res = infrastructure.process_message(
        {
            "module": "sentinel",
            "action": "update_settings",
            "kind": "request",
            "data": {"eula": 99, "token": token},
        }
    )
    assert res["data"]["eula"] == prev_eula

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["eula"] == prev_eula


def test_get_eula(file_root_init, infrastructure, uci_configs_init):
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_eula", "kind": "request"}
    )
    assert "data" in res
    assert res["data"] == {"version": 2, "text": "Second version\n"}

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_eula", "kind": "request", "data": {"version": 2}}
    )
    assert "data" in res
    assert res["data"] == {"version": 2, "text": "Second version\n"}

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_eula", "kind": "request", "data": {"version": 1}}
    )
    assert "data" in res
    assert res["data"] == {"version": 1, "text": "First version\n"}

    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_eula", "kind": "request", "data": {"version": 99}}
    )
    assert "data" in res
    assert res["data"] == {"version": 99, "text": None}


@pytest.mark.only_backends(["openwrt"])
def test_get_than_update(
    updater_userlists, updater_languages, file_root_init, infrastructure, init_script_result, uci_configs_init
):
    uci = get_uci_module(infrastructure.name)

    # initialize sentinel
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {"eula": 1}}
    )
    # get default settings
    assert "errors" not in res.keys()
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    token = res["data"]["token"]

    # modules are on true by default, change some
    modules = res["data"]["modules"]
    modules["survey"]["enabled"] = False

    # protocols are on by defualt, turn some off
    protocols = res["data"]["modules"]["minipot"]["protocols"]
    protocols["http"] = False
    protocols["telnet"] = False
    modules["minipot"]["protocols"] = protocols

    # you won't need to get installed status from UI
    for _, data in modules.items():
        data.pop("installed")

    # update settings
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {
            "token": token,
            "eula": 1,
            "modules": modules
        }}
    )
    assert "errors" not in res.keys()

    with uci.UciBackend(UCI_CONFIG_DIR_PATH) as uci_backend:
        data = uci_backend.read()

    assert uci.get_option_named(data, "sentinel", "minipot", "http_port", "") == "0"
    assert uci.get_option_named(data, "sentinel", "minipot", "telnet_port", "") == "0"

    # assert changes applied
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert "errors" not in res.keys()
    assert res["data"]["modules"]["survey"]["enabled"] is False
    minipot_prot = res["data"]["modules"]["minipot"]["protocols"]
    assert minipot_prot["http"] is False
    assert minipot_prot["telnet"] is False


@pytest.mark.parametrize(
    "sentinel_status",
    [
        ("RUNNING", "SENDING", "DISABLED", "FAILED"),
        ("SENDING", "DISABLED", "FAILED", "UNKNOWN"),
    ],
    indirect=True
)
def test_get_state(file_root_init, infrastructure, sentinel_status):
    """ Test getting sentinel components state

    We do not care about particular values here, it just need to be valid state
    """
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_state", "kind": "request"}
    )

    assert "error" not in res

    valid_states = ["running", "sending", "disabled", "failed", "unknown", "uninstalled"]
    assert res["data"]["fwlogs"] in valid_states
    assert res["data"]["minipot"] in valid_states
    assert res["data"]["survey"] in valid_states
    assert res["data"]["proxy"] in valid_states


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize(
    "sentinel_status,expected_states",
    [
        (
            ("RUNNING", "SENDING", "DISABLED", "FAILED"),
            ("running", "sending", "disabled", "failed")
        ),
        (
            ("SENDING", "DISABLED", "FAILED", "UNKNOWN"),
            ("sending", "disabled", "failed", "unknown")
        )
    ],
    indirect=["sentinel_status"]
)
def test_get_different_valid_states(file_root_init, infrastructure, sentinel_status, expected_states):
    """ Test multiple valid states """
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_state", "kind": "request"}
    )

    assert "error" not in res

    assert res["data"]["fwlogs"] == expected_states[0]
    assert res["data"]["minipot"] == expected_states[1]
    assert res["data"]["survey"] == expected_states[2]
    assert res["data"]["proxy"] == expected_states[3]


@pytest.mark.only_backends(["openwrt"])
@pytest.mark.parametrize("sentinel_status", [("FOO", "bAr", "Quux", "SomethingCompletelyDifferent")], indirect=True)
def test_get_unexpected_states(file_root_init, infrastructure, sentinel_status):
    """ Test that even with unexpected states, backend would return default value 'unknown' """
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_state", "kind": "request"}
    )

    assert "error" not in res

    assert res["data"]["fwlogs"] == "unknown"
    assert res["data"]["minipot"] == "unknown"
    assert res["data"]["survey"] == "unknown"
    assert res["data"]["proxy"] == "unknown"


@pytest.mark.only_backends(["openwrt"])
def test_get_malformed_states(file_root_init, infrastructure, sentinel_status_malformed_data):
    """ Test that even with malformed data, backend would return state 'uninstalled'"""
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_state", "kind": "request"}
    )

    assert "error" not in res

    assert res["data"]["fwlogs"] == "uninstalled"
    assert res["data"]["minipot"] == "uninstalled"
    assert res["data"]["survey"] == "uninstalled"
    assert res["data"]["proxy"] == "uninstalled"
