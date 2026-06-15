#!/bin/bash
apt-get update
apt-get install -y build-essential \
    libz-dev \
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    libssl-dev \
    libffi-dev \
    liblzma-dev \
    libbz2-dev

pip install -r requirements.txt
