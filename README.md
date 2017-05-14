# Byrbt-Autoseed
An Autoseed used to reseed TV-series and Anime in Some PT sites. \
Dome : [R酱 の 更新姬 - autoseed.rhilip.info](//autoseed.rhilip.info/) \
\
[![GitHub license](https://img.shields.io/badge/license-AGPL-blue.svg)](https://raw.githubusercontent.com/Rhilip/Pt-Autoseed/master/LICENSE)

## Support Site
| Site | URL | Supported Date |
|:------------------:|:---:|:---:|
| 北邮人BT | <https://bt.byr.cn/> | 2017-02-07 |
| 蒲公英 NPUBits | <https://npupt.com/> | 2017-05-12 |

## Based Environment
#### Ubtuntu 14.04, Python > 3.4.
* Transmission
```
apt-get -y install software-properties-common
add-apt-repository -y ppa:transmissionbt/ppa
apt-get update
apt-get -y install transmission-cli transmission-common transmission-daemon
```
* Flexget
```
apt-get -y install python-pip
pip install flexget
```
* rtorrent + irssi-autodl
```
wget --no-check-certificate https://raw.githubusercontent.com/arakasi72/rtinst/master/rtinst.sh
bash rtinst.sh -t
```
* MySQL
```
apt-get -y install mysql-server
```
* MediaInfo
```
apt-get -y install mediainfo
```
* ~~ffmpeg~~(rtinst.sh will install it)
```
apt-add-repository -y ppa:mc3man/trusty-media
apt-get update
apt-get -y install ffmpeg
```
* Python3 model
```
apt-get -y install python3-pip python3-lxml
pip3 install pymysql transmissionrpc requests bs4 pymediainfo
```
* Supervisor (Suggest)
```
pip install supervisor
```

## How to Use
```
cp setting.py usersetting.py
vi usersetting.py
sudo python3 autoseed.py
```