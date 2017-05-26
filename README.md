# PT-Autoseed
An Autoseed used to reseed TV-series and Anime in Some PT sites. \
The Reseed List: Saw Gist [Rhilip/Reseed List](https://gist.github.com/Rhilip/34ad82070d71bb3fa75f293d24101588) please.\
\
[![GitHub license](https://img.shields.io/badge/license-AGPL-blue.svg)](https://raw.githubusercontent.com/Rhilip/Pt-Autoseed/master/LICENSE)

## Support Site
| Site | URL | Supported Date |
|:------------------:|:---:|:---:|
| 北邮人BT | <https://bt.byr.cn/> | 2017-02-07 |
| 蒲公英 NPUBits | <https://npupt.com/> | 2017-05-12 |
| 麦田 PT | <http://pt.nwsuaf6.edu.cn/> | 2017-05-26 |

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
pip install flexget transmissionrpc
```
* rtorrent + irssi-autodl
```
wget --no-check-certificate https://raw.githubusercontent.com/arakasi72/rtinst/master/rtinst.sh
bash rtinst.sh -t
```
* MySQL (Use a remote mysqld alternative is feasible)
```
apt-get -y install mysql-server
```
* ~~MediaInfo~~ (rtinst.sh will install it)
```
apt-get -y install mediainfo
```
* ~~ffmpeg~~ (rtinst.sh will install it)
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

## Contribute
* Fork the repository on GitHub to start making your changes to the master branch (or branch off of it).
* Help to fix and update the reseed torrent's description.
* If the funds permit, please donate to help me update this repo and the autoseed server.

| WeChat | Alipay |
|:---:|:---:|
| <img src="https://blog.rhilip.info/wp-content/uploads/2017/05/wechat-e1494641989576.png" width = "300" > | <img src="https://blog.rhilip.info/wp-content/uploads/2017/04/alipay-e1494642034126.jpg" width = "300" > |