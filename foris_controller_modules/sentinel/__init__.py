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

import logging

from foris_controller.module_base import BaseModule
from foris_controller.handler_base import wrap_required_functions


class SentinelModule(BaseModule):
    logger = logging.getLogger(__name__)

    def action_get_settings(self, data: dict):
        """ Get configuration of sentinel
        :param data: {}
        :returns: {"eula": 0..X, "token": "..."/None}
        """
        return self.handler.get_settings()

    def action_update_settings(self, data):
        """ Update configuration of sentinel
        :param data: {"eula": 0..X} or {"eula": 0..X, "token": "..."}
        :returns: {"result": ..., "eula": 0..X, "token": "..."} or {"result": ..., "eula": 0..X}
        """
        res, eula, token = self.handler.update_settings(**data)
        if res:
            self.notify("update_settings", {"eula": eula})

        if token:
            return {"result": res, "eula": eula, "token": token}

        return {"result": res, "eula": eula}

    def action_get_fakepot_settings(self, data: dict):
        """ Get configuration of sentinel
        :param data: {}
        :returns: {"enabled": True/False, "extra_option": "..."}
        """
        return self.handler.get_fakepot_settings()

    def action_update_fakepot_settings(self, data):
        """ Update configuration of sentinel
        :param data: {"enabled": True/False, "extra_option": "..."}
        :returns: {"result": True/False}
        """

        res = self.handler.update_fakepot_settings(**data)
        self.notify("update_fakepot_settings", data)
        return {"result": res}

    def action_get_eula(self, data: dict):
        """ Get configuration of sentinel
        :param data: {} or {"version": X}
        :returns: {"version": X, "text": "blahblah"}
        """
        return self.handler.get_eula(**data)

    def action_get_state(self, data: dict):
        """ Get state of sentinel components """
        return self.handler.get_state()


@wrap_required_functions(
    [
        "get_settings",
        "update_settings",
        "get_fakepot_settings",
        "update_fakepot_settings",
        "get_eula",
        "get_state",
    ]
)
class Handler(object):
    pass
