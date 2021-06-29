#
# foris-controller-sentinel-module
# Copyright (C) 2019-2021 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
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

import typing
import logging

from secrets import token_hex

from foris_controller.handler_base import BaseMockHandler
from foris_controller.utils import logger_wrapper

from .. import Handler

logger = logging.getLogger(__name__)


class MockSentinelHandler(Handler, BaseMockHandler):

    eulas: typing.Dict[int, str] = {1: "First version\n", 2: "Second version\n"}
    valid_eulas: typing.List[int] = [0] + list(eulas.keys())

    eula: int = 0
    token: typing.Optional[str] = None
    fakepot_enabled: bool = False
    fakepot_extra_option: str = ""
    fake_modules: typing.Dict[str,typing.Union[bool, typing.Dict[str, bool]]] = {
        "minipot": {
            "enabled": True,
            "installed": True,
            "protocols": {
                "ftp": True,
                "http": True,
                "smtp": False,
                "telnet": False
            }
        },
        "fwlogs": {
            "enabled": True,
            "installed": True
        },
        "survey": {
            "enabled": True,
            "installed": True
        }
    }

    @logger_wrapper(logger)
    def get_settings(self) -> dict:
        return {
            "eula": MockSentinelHandler.eula,
            "token": MockSentinelHandler.token,
            "modules": MockSentinelHandler.fake_modules
        }

    @logger_wrapper(logger)
    def update_settings(
        self, eula: int, token: typing.Optional[str] = None,
        modules: typing.Optional[typing.Dict[str,bool]] = None,
        protocols: typing.Optional[typing.Dict[str,bool]] = None
    ) -> typing.Tuple[bool, int, typing.Optional[str]]:
        if eula not in MockSentinelHandler.valid_eulas:
            return False, MockSentinelHandler.eula, None

        MockSentinelHandler.eula = eula

        if eula == 0:
            return True, eula, None

        if token is not None:
            MockSentinelHandler.token = token
        elif MockSentinelHandler.token is None:
            MockSentinelHandler.token = token_hex(32)

        return True, eula, MockSentinelHandler.token

    @logger_wrapper(logger)
    def get_fakepot_settings(self) -> dict:
        return {
            "enabled": MockSentinelHandler.fakepot_enabled,
            "extra_option": MockSentinelHandler.fakepot_extra_option,
        }

    @logger_wrapper(logger)
    def update_fakepot_settings(self, enabled: bool, extra_option: str) -> bool:
        MockSentinelHandler.fakepot_enabled = enabled
        MockSentinelHandler.fakepot_extra_option = extra_option
        return True

    @logger_wrapper(logger)
    def get_eula(self, version: typing.Optional[int] = None) -> dict:
        version = version or max(MockSentinelHandler.eulas.keys())

        return {"version": version, "text": MockSentinelHandler.eulas.get(version)}

    @staticmethod
    @logger_wrapper(logger)
    def get_state() -> typing.Dict[str, str]:
        return {
            "fwlogs": "running",
            "survey": "running",
            "minipot": "running",
            "proxy": "running",
        }
