# My Home Assistant Config

## login to ResinOS using SSH

1. Remove the SD-Card from your RPI and connect it to a computer
2. Create an authorized_keys file in the root of the resin-boot volume
3. Append your public key to the file.
4. Reinsert the SD-Card to the RPI and restart it
5. Login to the RPI using SSH on port 22222
   ```bash
   ssh root@hassio.local -p 22222
   ```
6. You are logged in.

## Access the Tellstick container when running hassio
```bash
docker exec -it addon_core_tellstick /bin/bash
```

## Observe tellcore events within the Tellstick container when running Hass.io
```bash
apk add py-pip && pip install tellcore-py && tellcore_events --raw
```

## Tellstick config
```json
{
  "devices": [
    {
      "id": 1,
      "name": "desktop",
      "protocol": "arctech",
      "model": "selflearning-switch",
      "house": "28622",
      "unit": "1"
    },
    {
      "id": 2,
      "name": "bathroom_ceiling",
      "protocol": "arctech",
      "model": "selflearning-switch",
      "house": "14409345",
      "unit": "2"
    },
    {
      "id": 3,
      "name": "hallway_ceiling",
      "protocol": "arctech",
      "model": "selflearning-dimmer",
      "house": "14409345",
      "unit": "3"
    },
    {
      "id": 4,
      "name": "toaster",
      "protocol": "arctech",
      "model": "selflearning-switch",
      "house": "27982",
      "unit": "5"
    },
    {
      "id": 5,
      "name": "nexa_remote_g",
      "protocol": "arctech",
      "model": "selflearning-switch",
      "house": "12039998",
      "unit": "16"
    }
  ]
}
```

## Multiple triggers

[Multiple Triggers](https://www.home-assistant.io/docs/automation/trigger/#multiple-triggers)

## AppDaemon
https://github.com/ReneTode/My-AppDaemon/blob/master/AppDaemon_for_Beginner/Part_1(listen_state_and_get_state).md

## Hassio Addons
https://github.com/home-assistant/hassio-addons

## Remove derelict entities
Sometimes old discovered devices hangs around. They can be removed from HomeAssistant by removing
them from the file `/config/.storage/core.device_registry.yml`



