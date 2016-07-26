#!/bin/bash

cp /vagrant/resources/saslauthd-postfix /etc/default/.
rm -r /run/saslauthd
ln -s /var/spool/postfix/var/run/saslauthd /run/saslauthd
dpkg-statoverride --add root sasl 710 /var/spool/postfix/var/run/saslauthd
