import sys
from collections import namedtuple

import oneagent

# pylint:disable=protected-access

MockVerInfo = namedtuple("MockVerInfo", "major minor patch releaselevel serial")

def test_pyversion_beta(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', MockVerInfo(5, 4, 3, 'beta', 123))
    assert oneagent._get_py_version() == '5.4.3beta123'

def test_pyversion_final(monkeypatch):
    monkeypatch.setattr(sys, 'version_info', MockVerInfo(5, 4, 3, 'final', 0))
    assert oneagent._get_py_version() == '5.4.3'

def test_py_edition():
    assert oneagent._get_py_edition()
