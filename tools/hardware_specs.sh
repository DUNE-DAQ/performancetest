#!/bin/bash
sudo lshw -html > /tmp/$HOSTNAME-lshw.html

weasyprint /tmp/$HOSTNAME-lshw.html $HOSTNAME-lshw.pdf
echo "Created $HOSTNAME-lshw.pdf"

sudo dmidecode > $HOSTNAME-dmidecode.doc

echo "Created $HOSTNAME-dmidecode.doc"
