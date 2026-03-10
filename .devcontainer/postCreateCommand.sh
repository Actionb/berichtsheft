#!/bin/sh

echo "alias uv='uv --native-tls'" >> /etc/bash.bashrc
uv --native-tls pip install -r ./requirements.txt
uv --native-tls pip install --group dev