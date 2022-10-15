import asyncio
from dataclasses import dataclass, field
from threading import Thread
from time import sleep
from typing import Dict
from kasa import SmartPlug, SmartDevice, Discover

TRIGGER = 'TRIGGER'
TARGET = 'TARGET'

DISCOVERY_SLEEP_S = 60
POLL_SLEEP_S = 0.5

@dataclass
class SwitchGroup:
    name: str
    state: bool = None
    triggers: 'list[SmartPlug]' = field(default_factory=lambda: [])
    targets: 'list[SmartPlug]' = field(default_factory=lambda: [])
    

class DiscoveryProcess:

    def __init__(self):
        self.switch_groups: 'dict[str, SwitchGroup]' = {}
        self.last_name_list = []
        self.thread_ref = Thread(target=self.thread, daemon=True)
        self.thread_ref.start()
    
    async def discover(self):
        devices: Dict[str, SmartDevice] = await Discover.discover()
        if devices.keys() == self.last_name_list:
            return
        self.last_name_list = devices.keys()
        switch_groups: 'dict[str, SwitchGroup]' = {}
        for value in devices.values():
            # Format of names should be <GROUP>-<TRIGGER|TARGET>-<DISAMBIGUATOR>
            name_parts = value.alias.upper().split('-')
            if len(name_parts) == 3 and (name_parts[1] == TRIGGER or name_parts[1] == TARGET):
                group = name_parts[0]
                if switch_groups.get(group) is None:
                    switch_groups[group] = SwitchGroup(group)
                if name_parts[1] == TRIGGER:
                    switch_groups[group].triggers.append(SmartPlug(value.host))
                elif name_parts[1] == TARGET:
                    switch_groups[group].targets.append(SmartPlug(value.host))
        print('Discovered new groups: ', switch_groups)
        self.switch_groups = switch_groups

    def thread(self):
        while True:
            asyncio.run(self.discover())
            sleep(DISCOVERY_SLEEP_S)

    @property
    def is_alive(self):
        return self.thread_ref.is_alive()



async def auto_monitor(discovery: DiscoveryProcess):
    switch_groups = {}
    while True:
        switch_groups = discovery.switch_groups
        update_list = []
        for g in switch_groups.values():
            update_list = update_list + g.triggers
        if not discovery.is_alive:
            raise Exception('Error in DiscoveryProcess')
        # Update all triggers concurrently for efficiency
        await asyncio.gather(*[trigger.update() for trigger in update_list])
        for group in switch_groups.values():
            changed_triggers = list(filter(lambda trigger: trigger.is_on != group.state, group.triggers))
            if (len(changed_triggers) > 0):
                # The first one that is different is the source of truth.  That way all triggers will get aligned on startup
                group.state = changed_triggers[0].is_on
                other_triggers = list(filter(lambda trigger: trigger.is_on != group.state, group.triggers))
                print(f"Changing state of {group.name} to {group.state}")
                if (group.state):
                    [await target.turn_on() for target in group.targets + other_triggers]
                else:
                    [await target.turn_off() for target in group.targets + other_triggers]
        await asyncio.sleep(POLL_SLEEP_S)


if __name__ == "__main__":
    discovery = DiscoveryProcess()
    asyncio.run(auto_monitor(discovery))
