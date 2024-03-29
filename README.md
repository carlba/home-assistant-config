# My Home Assistant Config

## Common Gotchas

If a automation refuses to start validate that it's state is on.

### Remove derelict entities

Sometimes old discovered devices hangs around. They can be removed from HomeAssistant by

1. Removing them from the file `/config/.storage/core.device_registry.yml`.
2. Changing the name of the duplicated entry in core.entity_registry i.e
   light.desktop_2 -> light.desktop.
3. Restarting HomeAssistant.

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

[Info about Xiaomi -> HA integration](https://www.home-assistant.io/integrations/xiaomi_miio)

A token is required to access and control the device it can be retrieved, like so:

1. Install an BlueStacks emulator

   ```bash
    brew install --cask bluestacks
   ```

2. Install [MiHome v5.4.49](https://www.apkmirror.com/apk/xiaomi-inc/mihome/mihome-5-4-49-release)
   It has to be this exact release which both writes the token to the sqlite DB and supports the
   european servers. Earlier and later versions don't fulfill both these requirements.

3. Using v5.4.49 of Mi Home locate a text file under the Smarthome/logs folder where the
   32 character token is stored.

   ```bash
   adb pull /storage/self/primary/SmartHome/logs/plug_DeviceManager/2021-05-25.txt
   ```

### Getting the room mappings

1. Install the miio CLI

   ```bash
   npm install -g miio
   ```

2. Add token of vacuum to the settings of the CLI

   ```bash
   miio tokens update 192.168.1.11 --token <TOKEN>
   ```

## Xiaomi Speedfan C1

[HA Xiaomi Speedfan C1 Custom Component](https://github.com/syssi/xiaomi_fan)

## Lovelace UI

Icons can be found at http://materialdesignicons.com

## AppDaemon

https://github.com/ReneTode/My-AppDaemon/blob/master/AppDaemon_for_Beginner/Part_1(listen_state_and_get_state).md

## Hassio Addons

https://github.com/home-assistant/hassio-addons

## home-assistant-cli

```bash
brew install homeassistant-cli
```

## Testing automation's

There are a few caveats when doing automation's

1. When an automation is triggered from entities the condition is not applied.
2. The best way to test them is to just manually change the state of the sensor that is
   just to trigger the automation.

## Deconz

### Finding your Events

dash://homeassistant:deconz

Navigate to Developer tools->Events. In the section Listen to events add deconz_event and press
START LISTENING. All events from deCONZ will now be shown and by pushing your remote button while
monitoring the log it should be fairly easy to find the events you are looking for.

### Debugging

```yaml
pydeconz: debug
homeassistant.components.deconz: debug
```

### Customizing entities

Items on the lovelace dashboard can be customized by adding them to `customize.yml`, like so:

```yaml
script.dinner:
  icon: mdi:food
```

This [site](https://pictogrammers.github.io/@mdi/font/3.2.89) will show which icons are available.

## TODO
