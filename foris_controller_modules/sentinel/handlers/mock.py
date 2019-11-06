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

import typing
import logging

from secrets import token_hex

from foris_controller.handler_base import BaseMockHandler
from foris_controller.utils import logger_wrapper

from .. import Handler

logger = logging.getLogger(__name__)


class MockSentinelHandler(Handler, BaseMockHandler):

    eula: int = 0
    token: typing.Optional[str] = None
    fakepot_enabled: bool = False
    fakepot_extra_option: str = ""

    @logger_wrapper(logger)
    def get_settings(self) -> dict:
        return {"eula": MockSentinelHandler.eula, "token": MockSentinelHandler.token}

    @logger_wrapper(logger)
    def update_settings(
        self, eula: int, token: typing.Optional[str] = None
    ) -> typing.Optional[str]:
        MockSentinelHandler.eula = eula

        if eula == 0:
            return None

        if token is not None:
            MockSentinelHandler.token = token
        elif MockSentinelHandler.token is None:
            MockSentinelHandler.token = token_hex(32)

        return MockSentinelHandler.token

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
