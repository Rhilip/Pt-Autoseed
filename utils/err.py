# ！/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2017-2020 Rhilip <rhilipruan@gmail.com>

__package__ = ["ReseedError", "NoCloneTorrentError", "CannotAssistError"]


class ReseedError(OSError):
    pass


class NoCloneTorrentError(ReseedError):
    pass


class CannotAssistError(ReseedError):
    pass


class NoMatchPatternError(ReseedError):
    pass
