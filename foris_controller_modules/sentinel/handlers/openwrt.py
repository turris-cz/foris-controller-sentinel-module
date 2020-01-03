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

import logging
import typing

from foris_controller.handler_base import BaseOpenwrtHandler
from foris_controller.utils import logger_wrapper

from foris_controller_backends.sentinel import SentinelUci, SentinelEulas

from .. import Handler

logger = logging.getLogger(__name__)


class OpenwrtSentinelHandler(Handler, BaseOpenwrtHandler):

    uci = SentinelUci()
    eulas = SentinelEulas()

    @logger_wrapper(logger)
    def get_settings(self) -> dict:
        return OpenwrtSentinelHandler.uci.get_settings()

    @logger_wrapper(logger)
    def update_settings(
        self, eula: int, token: typing.Optional[str] = None
    ) -> typing.Tuple[bool, int, typing.Optional[str]]:
        return OpenwrtSentinelHandler.uci.update_settings(eula, token)

    @logger_wrapper(logger)
    def get_fakepot_settings(self) -> dict:
        return OpenwrtSentinelHandler.uci.get_fakepot_settings()

    @logger_wrapper(logger)
    def update_fakepot_settings(self, enabled: bool, extra_option: str) -> bool:
        return OpenwrtSentinelHandler.uci.update_fakepot_settings(enabled, extra_option)

    @logger_wrapper(logger)
    def get_eula(self, version: typing.Optional[int] = None) -> dict:
        return OpenwrtSentinelHandler.eulas.get_eula(version)
