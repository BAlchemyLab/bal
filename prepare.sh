#!/bin/bash
cat >/etc/yum.repos.d/naulinux-extras.repo <<EOL
[naulinux-extras]
name=NauLinux Extras
baseurl=http://downloads.naulinux.ru/pub/NauLinux/7/\$basearch/Extras/RPMS/
enabled=0
gpgcheck=1
gpgkey=http://downloads.naulinux.ru/pub/NauLinux/RPM-GPG-KEY-linux-ink
EOL
yum install -y nano epel-release
yum install --enablerepo=naulinux-extras -y openvswitch mininet ryu
systemctl restart openvswitch
