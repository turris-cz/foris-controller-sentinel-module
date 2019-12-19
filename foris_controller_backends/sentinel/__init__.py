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

from secrets import token_hex

from foris_controller_backends.files import BaseFile
from foris_controller_backends.services import OpenwrtServices
from foris_controller_backends.uci import UciBackend, get_option_named, parse_bool, store_bool


SENTINEL_MODULES = {
    "fakepot": {
        "hooks": [("sentinel", "reload"), ("sentinel", "restart")],
        "updater_flag": "fakepot",
    }
}

logger = logging.getLogger(__name__)


class SentinelUci:
    def _read_uci(self):
        with UciBackend() as backend:
            return backend.read("sentinel")

    def _get_valid_eulas(self):
        content = BaseFile()._file_content("/usr/share/sentinel-eula/EULAs.csv")
        res = [0]

        for line in content.splitlines(False):
            try:
                res.append(int(line.split(",")[0]))
            except (ValueError, IndexError):
                pass

        return res

    def get_settings(self):
        data = self._read_uci()
        eula = int(get_option_named(data, "sentinel", "main", "agreed_with_eula_version", "0"))
        token = get_option_named(data, "sentinel", "main", "device_token", "") or None
        return {"eula": eula, "token": token}

    def update_settings(self, eula, token=None):

        valid_eulas = self._get_valid_eulas()
        if eula not in valid_eulas:
            data = self.get_settings()
            return False, data["eula"], None

        with UciBackend() as backend:
            data = backend.read("sentinel")

            backend.add_section("sentinel", "main", "main")
            # TODO check whether eula number matches current eula number
            backend.set_option("sentinel", "main", "agreed_with_eula_version", eula)

            # update token
            data = backend.read("sentinel")
            stored_token = get_option_named(data, "sentinel", "main", "device_token", "") or None
            if token is None and stored_token is None:
                logger.debug("Generating new token")
                token = token_hex(32)

            if token:
                backend.set_option("sentinel", "main", "device_token", token)

        with OpenwrtServices() as services:
            services.restart("sentinel")

        return True, eula, token if eula != 0 else None

    def get_fakepot_settings(self) -> dict:
        data = self._read_uci()

        enabled = parse_bool(get_option_named(data, "sentinel", "fakepot", "enabled", "0"))
        extra_option = get_option_named(data, "sentinel", "fakepot", "extra_option", "")
        return {"enabled": enabled, "extra_option": extra_option}

    def update_fakepot_settings(self, enabled, extra_option):
        with UciBackend() as backend:

            backend.add_section("sentinel", "fakepot", "fakepot")
            backend.set_option("sentinel", "fakepot", "enabled", store_bool(enabled))
            backend.set_option("sentinel", "fakepot", "extra_option", extra_option)

        with OpenwrtServices() as services:
            for service_name, action in SENTINEL_MODULES["fakepot"]["hooks"]:
                # try to perform an action (might not work if the fakepot is
                # currently being installed
                getattr(services, action)(service_name, fail_on_error=False)

        return True
