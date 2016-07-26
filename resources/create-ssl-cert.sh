#!/bin/bash

DEST=/etc/ssl/private
SUBJ="/C=TW/ST=TPE/L=Taipei/O=MedicusTek Inc/OU=Cloud R&D/CN=mail.medicustek.test"

echo 'Create SSL cert'
openssl req -x509 -subj "$SUBJ" -nodes -newkey rsa:1024 -keyout $DEST/mail.key -out $DEST/mail.crt -days 356

cat $DEST/mail.crt $DEST/mail.key > $DEST/mail.pem
chmod 640 $DEST/mail.key
chmod 640 $DEST/mail.pem
