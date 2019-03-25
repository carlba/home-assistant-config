# My Home Assistant Config

## Common Gotchas

If a automation refuses to start validate that it's state is on.

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
      "name": "bathroom_ceiling",
      "protocol": "arctech",
      "model": "selflearning-switch",
      "house": "14409345",
      "unit": "2"
    }
  ]
}
```

## Multiple triggers

[Multiple Triggers](https://www.home-assistant.io/docs/automation/trigger/#multiple-triggers)

## Xiaomi Roborock Mi S50

A token is required to access and control the device it can be retrieved, like so:

1. Install an Android Emulator.

2. Install [MiHome 5.0.9](https://www.apkmirror.com/apk/xiaomi-inc/mihome/mihome-5-0-9-release)
   It has to be this exact release which both writes the token to the sqlite DB and supports the 
   european servers. Earlier and later versions don't fulfill both these requirements.

3. Install Google Drive

4. Upload `/data/data/com.xiaomi.smarthome/databases/miio2.db` to Google Drive using any Android 
   file manager (Root is required).
   
5.  Download the file from Google Drive.

6. In the folder where you downloaded the sqlite db, execute:
   ```sqlite3 miio2.db 'select token from devicerecord'```

## AppDaemon
https://github.com/ReneTode/My-AppDaemon/blob/master/AppDaemon_for_Beginner/Part_1(listen_state_and_get_state).md

## Hassio Addons
https://github.com/home-assistant/hassio-addons

## Remove derelict entities
Sometimes old discovered devices hangs around. They can be removed from HomeAssistant by removing
them from the file `/config/.storage/core.device_registry.yml`



