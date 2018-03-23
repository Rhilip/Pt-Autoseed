# PT-Autoseed

An Autoseed used to reseed TV-series and Anime in Some PT sites. 

The Reseed List: Saw Gist [Rhilip/Reseed List](https://gist.github.com/Rhilip/34ad82070d71bb3fa75f293d24101588) please.

[![GitHub license](https://img.shields.io/badge/license-AGPL-blue.svg)](https://raw.githubusercontent.com/Rhilip/Pt-Autoseed/master/LICENSE)

## Support Site

| Site | URL | Supported Date |
|:------------------:|:---:|:---:|
| 北邮人BT | <https://bt.byr.cn/> | 2017-02-07 |
| 蒲公英 NPUBits | <https://npupt.com/> | 2017-05-12 |
| 麦田 PT | <https://pt.nwsuaf6.edu.cn/> | 2017-05-26 |
| 北洋园PT | <https://tjupt.org/> | 2017-06-23 |

## Based Environment

- Ubuntu 16.04.03, Python 3.5.2

* Transmission

```sh
apt-get -y install software-properties-common
add-apt-repository -y ppa:transmissionbt/ppa
apt-get update
apt-get -y install transmission-cli transmission-common transmission-daemon
```

* Flexget

```sh
apt-get -y install python-pip
pip install flexget transmissionrpc
```

* rtorrent + irssi-autodl (see [arakasi72/rtinst](https://github.com/arakasi72/rtinst))

```sh
bash -c "$(wget --no-check-certificate -qO - https://raw.githubusercontent.com/arakasi72/rtinst/master/rtsetup)"
rtinst
```

* MySQL (Use a remote mysqld alternative is feasible)

```sh
apt-get -y install mysql-server
```

* ~~MediaInfo~~ (rtinst.sh will install it)

```sh
apt-get -y install mediainfo
```

* ~~ffmpeg~~ (rtinst.sh will install it)

```sh
apt-add-repository -y ppa:mc3man/trusty-media
apt-get update
apt-get -y install ffmpeg
```

* Python3 model

```sh
apt-get -y install python3-pip python3-lxml
pip3 install pymysql transmissionrpc requests bs4
```

* Supervisor (Suggest)

```sh
apt-get install supervisor
```

## How to Use

```sh
git clone https://github.com/Rhilip/Pt-Autoseed.git
cd Pt-Autoseed
cp setting.py usersetting.py
vi usersetting.py
sudo python3 run.py

```
Notice: You should run the autoseed as root.
if no problem or error, You can use `screen` or other software like `supervisor` to keep it run in the background.

## Reseeder Setting

 - class extractors.base.site.Site

| Key in setting | Type | Default | Description |
|:---|:---:|:---:|:---|
| status | Boolean | False | Require, Reseeder enable status |
| cookies | Dict or String | None | Require, Cookies for reseeder site |
| extend_descr_before | Boolean | True | Enable to Enhanced the description of notice |
| extend_descr_thumbnails | Boolean | True | Enable to Enhanced the description of thumbnails |
| extend_descr_mediainfo | Boolean | True | Enable to Enhanced the description of mediainfo |
| extend_descr_cloneinfo | Boolean | True | Enable to Enhanced the description of cloneinfo |
| assist_only | Boolean | False | Enable to only assist the exist same torrent but not to reseed |

- class extractors.base.nexusphp.NexusPHP(Site)

| Key in setting | Type | Default | Description |
|:---|:---:|:---:|:---|
| anonymous_release | Boolean | True | Enable to Release anonymously |
| auto_thank | Boolean | True | Enable to Automatically thanks for additional Bones after Reseed |
| default_clone_torrent | Integer | None | When not find the clone torrent, use it as default clone_id |
| force_judge_dupe_loc | Boolean | False | Judge torrent is dupe or not in location before post it to PT-site. |
| get_clone_id_from_db | Boolean | True | Enable to get clone torrent's id from database first, then search. |
| allow_cat | List | None | Used to limit the reseed torrent category |

- class extractors.byrbt.Byrbt(NexusPHP)

| Key in setting | Type | Default | Description |
|:---|:---:|:---:|:---|
| no_subtitle | Boolean | False | NO subtitle when POST |

- class extractors.tjupt.TJUPT(NexusPHP)

| Key in setting | Type | Default | Description |
|:---|:---:|:---:|:---|
| torrent_visible | Boolean | True | Display In the browse page (Dead torrent will be set if not checked) |

## Contribute

* Fork the repository on GitHub to start making your changes to the master branch (or branch off of it).
* Help to fix and update the reseed torrent's description.
* If the funds permit, please donate to help me update this repo and the autoseed server.

| WeChat | Alipay | QQ |
|:---:|:---:|:---:|
| <img src="https://blog.rhilip.info/usr/uploads/my/wechat.jpg" width = "260" > | <img src="https://blog.rhilip.info/usr/uploads/my/alipay.jpg" width = "260" > | <img src="https://blog.rhilip.info/usr/uploads/my/qq.jpg" width = "260" > |