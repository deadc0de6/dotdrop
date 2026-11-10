"""Non-positive --workers values must be rejected with a usage error."""

import os

import pytest

from dotdrop.options import Options

from tests.helpers import _fake_args, create_fake_config, populate_fake_config


def _options_with_workers(tmp_path, monkeypatch, workers):
    monkeypatch.delenv('DOTDROP_WORKERS', raising=False)
    confpath = create_fake_config(str(tmp_path))
    populate_fake_config(confpath, profiles={'host1': {'dotfiles': []}})
    args = _fake_args()
    args['--cfg'] = confpath
    args['--profile'] = 'host1'
    args['--workers'] = workers
    args['install'] = True
    return Options(args=args)


def test_workers_zero_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr('dotdrop.settings.is_bin_in_path', lambda command: True)
    with pytest.raises(SystemExit):
        _options_with_workers(tmp_path, monkeypatch, 0)


def test_workers_negative_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr('dotdrop.settings.is_bin_in_path', lambda command: True)
    with pytest.raises(SystemExit):
        _options_with_workers(tmp_path, monkeypatch, -3)


def test_workers_positive_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr('dotdrop.settings.is_bin_in_path', lambda command: True)
    assert _options_with_workers(tmp_path, monkeypatch, 2).workers == 2
