set dotenv-load := true

setup_dev_environment:
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt

sync:
    rsync -v -r --update --exclude 'venv' --exclude '.idea' --exclude '.git' --exclude '.vscode' --exclude 'resources' --exclude '__pycache__' -P  ./ $HASS_SYNC_PATH

reload:
    venv/bin/hass-cli -x service call homeassistant.restart

reload-automations:
    venv/bin/hass-cli -x service call automation.reload

reload-scripts:
    venv/bin/hass-cli -x service call script.reload

reload-groups:
    venv/bin/hass-cli -x service call script.reload