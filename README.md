# Raspberry Pi Setup

On the pi, run `pip install python-kasa`.  Change `pi` in `kasa.service` to your username.  `mv` or `scp` the script to `~/` and the `kasa.service` to `/lib/systemd/system/`.  Use stardard systemctl commands to manage the service, i.e.

```
# start the service
sudo systemctl start kasa.service
# register the service to start at boot
sudo systemctl enable kasa.service
```

# Smart Device setup

Register your switches on the Kasa app or python-kasa using the following format.

`<GROUP>-<TRIGGER|TARGET>-<DISAMBIGUATOR>`

ex: `LIVING_ROOM-TRIGGER-WALL_SWITCH`
    `LIVING_ROOM-TARGET-FLOOR_LAMP`

This automatically creates a group called `LIVING_ROOM` and tells the script about the triggers or sources.  The disambiguator isn't used by the script, it's for human-readable purposes only.  Just make sure that you use `-` only in the designated places.  Any device that you don't want monitored by the script can be called anything, as long as it's not a `TRIGGER` or `TARGET` it's ignored. 

You can also create Kasa smart routines for the switch as a backup, if desired.  Both can be active at the same time.