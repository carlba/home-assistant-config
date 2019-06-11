#!/usr/bin/env bash
[[ ! -d 'custom_components' ]] && mkdir custom_components
[[ ! -d 'www' ]] && mkdir www

(cd www && curl -OL 'https://github.com/kalkih/mini-media-player/releases/download/v0.9.2/mini-media-player-bundle.js')

(cd www && curl -OL 'https://raw.githubusercontent.com/thomasloven/lovelace-slider-entity-row/master/slider-entity-row.js')

# https://github.com/custom-cards/light-entity-row
(cd www && curl -OL 'https://raw.githubusercontent.com/custom-cards/light-entity-row/master/light-entity-row.js')

# https://github.com/custom-cards/circle-sensor-card
(cd www && curl -OL 'https://raw.githubusercontent.com/custom-cards/circle-sensor-card/master/circle-sensor-card.js')

[[ ! -d 'www/custom-lovelace/swipe-card' ]] && mkdir -p www/custom-lovelace/swipe-card

(cd www/custom-lovelace/swipe-card && curl -OL 'https://raw.githubusercontent.com/bramkragten/custom-ui/master/swipe-card/swipe-card.js')

cd ..
ln -s addons ../addons
