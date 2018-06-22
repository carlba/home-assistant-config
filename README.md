# My Home Assistant Config

## login to ResinOS using SSH

1. Remove the SD-Card from your RPI and connect it to a computer
2. Create an authrized_keys file in the root of the resin-boot volume
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