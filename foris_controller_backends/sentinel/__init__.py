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
import typing
import csv
import os

from io import StringIO
from secrets import token_hex

from foris_controller_backends.cmdline import BaseCmdLine
from foris_controller_backends.files import BaseFile
from foris_controller_backends.uci import UciBackend, get_option_named, parse_bool, store_bool, UciException

logger = logging.getLogger(__name__)


class SentinelUci:
    _MINIPOT_PROTOCOLS = ["ftp", "http", "smtp", "telnet"]
    _SENTINEL_MODULES = ["minipot", "nikola", "survey"]

    def _read_uci(self):
        with UciBackend() as backend:
            return backend.read("sentinel")

    def get_settings(self):
        data = self._read_uci()
        eula = int(get_option_named(data, "sentinel", "main", "agreed_with_eula_version", "0"))
        token = get_option_named(data, "sentinel", "main", "device_token", "") or None

        modules = {
            sentinel_module : parse_bool(get_option_named(data, "sentinel", sentinel_module, "enabled", "1"))
            for sentinel_module in SentinelUci._SENTINEL_MODULES
        }
        protocols = {
            protocol : False if get_option_named(data, "sentinel", "minipot", f"{protocol}_port", "1") == "0" else True
            for protocol in SentinelUci._MINIPOT_PROTOCOLS
        }

        return {
            "eula": eula,
            "token": token,
            "modules": modules,
            "protocols": protocols
        }

    def update_settings(self, eula, modules=None, protocols=None, token=None):

        valid_eulas = [e[0] for e in SentinelEulas.get_valid_eulas()]
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

            if modules is not None:
                for module in SentinelUci._SENTINEL_MODULES:
                    backend.add_section("sentinel", module, module)
                    backend.set_option("sentinel", module, "enabled", store_bool(modules[module]))

            if protocols is not None:
                for protocol in SentinelUci._MINIPOT_PROTOCOLS:
                    if protocols[protocol]:
                        try:
                            backend.del_option("sentinel", "minipot", f"{protocol}_port")
                        except UciException:
                            pass
                    else:
                        backend.set_option("sentinel", "minipot", f"{protocol}_port", "0")


        # Reload sentinel components
        BaseCmdLine._run_command_and_check_retval(["/usr/bin/sentinel-reload"], 0)

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

        return True


_EULAS_LIST = typing.List[typing.Tuple[int, typing.Optional[str]]]


class SentinelEulas:
    EULAS_PATH_PREFIX = "/usr/share/sentinel-eula"

    @staticmethod
    def get_valid_eulas() -> _EULAS_LIST:
        content = BaseFile()._file_content(
            os.path.join(SentinelEulas.EULAS_PATH_PREFIX, "EULAs.csv")
        )

        res = [(0, None)]

        io = StringIO(content)
        for version, path in csv.reader(io, delimiter=","):
            try:
                res.append((int(version), path.strip()))
            except ValueError:
                pass

        return res

    @staticmethod
    def get_eula(version: typing.Optional[int] = None) -> dict:
        text = None
        valid_eulas = dict(SentinelEulas.get_valid_eulas())
        del valid_eulas[0]
        if version is None:
            version = max(e for e in valid_eulas.keys())

        if version in valid_eulas:
            text = BaseFile()._file_content(
                os.path.join(SentinelEulas.EULAS_PATH_PREFIX, valid_eulas[version])
            )

        return {"version": version, "text": text}
