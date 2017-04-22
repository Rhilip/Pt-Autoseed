import setting

if setting.byr_reseed:
    from .byrbt import Byrbt as Autoseed


