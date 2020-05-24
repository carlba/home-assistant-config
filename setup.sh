#!/usr/bin/env bash
[[ ! -d 'custom_components' ]] && mkdir custom_components
[[ ! -d 'www' ]] && mkdir www

(cd www && curl -OL 'https://github.com/kalkih/mini-media-player/releases/download/v1.8.0/mini-media-player-bundle.js')

(cd www && curl -OL 'https://raw.githubusercontent.com/thomasloven/lovelace-slider-entity-row/master/slider-entity-row.js')

# https://github.com/custom-cards/circle-sensor-card
(cd www && curl -OL 'https://raw.githubusercontent.com/custom-cards/circle-sensor-card/master/circle-sensor-card.js')

# https://github.com/benct/lovelace-xiaomi-vacuum-card
(cd www && curl -OL 'https://raw.githubusercontent.com/benct/lovelace-xiaomi-vacuum-card/master/xiaomi-vacuum-card.js')

# https://maykar.github.io/custom-header/#installation/manual
(cd www && curl -OL 'https://github.com/maykar/custom-header/releases/download/1.3.8/custom-header.js')

[[ ! -d 'www/custom-lovelace/swipe-card' ]] && mkdir -p www/custom-lovelace/swipe-card
(cd www/custom-lovelace/swipe-card && curl -OL 'https://raw.githubusercontent.com/bramkragten/custom-ui/master/swipe-card/swipe-card.js')

# https://www.home-assistant.io/integrations/frontend
[[ ! -d 'themes' ]] && mkdir -p themes

# https://github.com/seangreen2/slate_theme
(cd themes && curl -OL 'https://raw.githubusercontent.com/seangreen2/slate_theme/master/themes/slate.yaml')
