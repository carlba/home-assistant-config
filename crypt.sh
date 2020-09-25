#!/bin/bash
if [[ -e secrets.yaml.enc ]]; then
  openssl aes-256-cbc -d -a -salt -in secrets.yaml.enc -out secrets.yaml
else
  openssl aes-256-cbc -a -salt -in secrets.yaml -out secrets.yaml.enc
fi
