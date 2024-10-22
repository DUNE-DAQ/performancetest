#!/bin/bash
sudo lshw -html > /tmp/$HOSTNAME-lshw.html

weasyprint /tmp/$HOSTNAME-lshw.html $HOSTNAME-lshw.pdf
echo "Created $HOSTNAME-lshw.pdf"

sudo dmidecode > /tmp/$HOSTNAME-dmidecode.txt
txt2pdf.py /tmp/$HOSTNAME-dmidecode.txt $HOSTNAME-dmidecode.txt

echo "Created $HOSTNAME-dmidecode.pdf"
