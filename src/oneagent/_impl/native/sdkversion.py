# -*- coding: utf-8 -*-
#
# Copyright 2018 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ctypes


class OnesdkStubVersion(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint32),
        ("minor", ctypes.c_uint32),
        ("patch", ctypes.c_uint32)]

    def __gt__(self, version):
        if not isinstance(version, OnesdkStubVersion):
            raise TypeError

        if self.major > version.major:
            return True
        elif self.major == version.major:
            if self.minor > version.minor:
                return True
            elif self.minor == version.minor:
                return self.patch > version.patch

        return False

    def __eq__(self, version):
        if not isinstance(version, OnesdkStubVersion):
            raise TypeError

        return self.major == version.major and \
            self.minor == version.minor and self.patch == version.patch

    def __ne__(self, version):
        return not self == version

    def __lt__(self, version):
        if not isinstance(version, OnesdkStubVersion):
            raise TypeError

        return not (self > version or self == version)

    def __ge__(self, version):
        return self > version or self == version

    def __le__(self, version):
        return self < version or self == version

    def __str__(self):
        return str(self.major) + '.' + str(self.minor) + '.' + str(self.patch)
