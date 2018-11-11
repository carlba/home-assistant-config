#!/usr/bin/env bash
[[ ! -d 'custom_components' ]] && mkdir custom_components
[[ ! -d 'www' ]] && mkdir www
(cd custom_components && curl -O 'https://raw.githubusercontent.com/custom-components/custom_updater/master/custom_components/custom_updater.py')
(cd www && curl -O 'https://raw.githubusercontent.com/custom-cards/tracker-card/master/tracker-card.js')
(cd www && curl -OL 'https://github.com/kalkih/mini-media-player/releases/download/v0.9.2/mini-media-player-bundle.js')
(cd www && curl -OL 'https://raw.githubusercontent.com/thomasloven/lovelace-slider-entity-row/master/slider-entity-row.js')

