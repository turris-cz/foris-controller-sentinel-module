#
# foris-controller-sentinel-module
# Copyright (C) 2019 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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
import secrets

from foris_controller_testtools.fixtures import (
    only_message_buses,
    backend,
    file_root_init,
    infrastructure,
    init_script_result,
    only_backends,
    start_buses,
    mosquitto_test,
    ubusd_test,
    uci_configs_init,
    notify_api,
    UCI_CONFIG_DIR_PATH,
)

from foris_controller_testtools.utils import get_uci_module, command_was_called


def test_get_settings(file_root_init, infrastructure, uci_configs_init, start_buses):
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert "error" not in res
    assert "data" in res
    assert "eula" in res["data"]
    assert "token" in res["data"]


def test_update_settings(
    file_root_init, infrastructure, start_buses, init_script_result, uci_configs_init
):
    filters = [("sentinel", "update_settings")]

    # once eula is set to be < 0 a token should be generated
    notifications = infrastructure.get_notifications(filters=filters)
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "update_settings", "kind": "request", "data": {"eula": 1}}
    )
    notifications = infrastructure.get_notifications(notifications, filters=filters)
    assert notifications[-1] == {
        u"module": "sentinel",
        u"action": "update_settings",
        u"kind": "notification",
        u"data": {"eula": 1},
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
        u"module": "sentinel",
        u"action": "update_settings",
        u"kind": "notification",
        u"data": {"eula": 0},
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
        u"module": "sentinel",
        u"action": "update_settings",
        u"kind": "notification",
        u"data": {"eula": 1},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_settings", "kind": "request"}
    )
    assert res["data"]["eula"] == 1
    assert res["data"]["token"] == token


@pytest.mark.only_backends(["openwrt"])
def test_update_settings_openwrt(
    file_root_init, infrastructure, start_buses, init_script_result, uci_configs_init
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


def test_get_fakepot_settings(file_root_init, infrastructure, uci_configs_init, start_buses):
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_fakepot_settings", "kind": "request"}
    )
    assert "error" not in res
    assert "data" in res
    assert "enabled" in res["data"]
    assert "extra_option" in res["data"]


def test_update_fakepot_settings(
    file_root_init, infrastructure, start_buses, init_script_result, uci_configs_init
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
        u"module": "sentinel",
        u"action": "update_fakepot_settings",
        u"kind": "notification",
        u"data": {"enabled": True, "extra_option": "first"},
    }
    res = infrastructure.process_message(
        {"module": "sentinel", "action": "get_fakepot_settings", "kind": "request"}
    )
    assert res["data"]["enabled"]
    assert res["data"]["extra_option"] == "first"


@pytest.mark.only_backends(["openwrt"])
def test_update_fakepot_settings_openwrt(
    file_root_init, infrastructure, start_buses, init_script_result, uci_configs_init
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
    file_root_init, infrastructure, start_buses, init_script_result, uci_configs_init
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


def test_get_eula(file_root_init, infrastructure, uci_configs_init, start_buses):
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
