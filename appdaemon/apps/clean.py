import appdaemon.plugins.hass.hassapi as hass


class ExtendedHass(hass.Hass):
    @hass.hass_check
    def timer_start(self, entity_id, duration=None, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        rargs = kwargs or {}
        rargs["entity_id"] = entity_id
        if duration:
                rargs["duration"] = duration
        self.call_service("timer/start", **rargs)

    @hass.hass_check
    def switch_on(self, entity_id, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        if kwargs == {}:
            rargs = {"entity_id": entity_id}
        else:
            rargs = kwargs
            rargs["entity_id"] = entity_id
        self.call_service("switch/turn_on", **rargs)

    @hass.hass_check
    def switch_off(self, entity_id, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        if kwargs == {}:
            rargs = {"entity_id": entity_id}
        else:
            rargs = kwargs
            rargs["entity_id"] = entity_id
        self.call_service("switch/turn_off", **rargs)

    @hass.hass_check
    def harmony_remote(self, entity_id, state, activity, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        if state not in ['on', 'off']:
            raise(TypeError, "state must be 'on' or 'off'")

        rargs = kwargs or {}
        rargs["entity_id"] = entity_id
        rargs["activity"] = activity

        self.call_service("remote/turn_{}".format(state), **rargs)


# noinspection PyAttributeOutsideInit
class Clean(ExtendedHass):

    def initialize(self):
        self.timer = 'timer.clean'
        self.previous_state = None
        self.triggered = False
        self.harmony_remote_listener = self.listen_state(self.tracker,
                                                         entity='remote.harmony_hub',
                                                         attribute='current_activity')
        self.listen_event(self.stop_cleaning, event='timer.finished', entity_id=self.timer)

    def tracker(self, entity, attribute, old, new, kwargs):
        self.previous_state = old
        self.log('Clean.tracker(): entity {}, old {}, new {}'.format(entity, old, new))
        self.log(kwargs)
        if not self.triggered:
            if new == 'Clean':
                self.start_cleaning()
            elif old != 'Clean' and new == 'Away':
                self.log('Starting cleaning in 10 seconds')
                self.run_in(self.start_cleaning, 10)
        else:
            pass
            # Handle when user manually cancels clean

    def start_cleaning(self, kwargs=None):
        self.triggered = True
        self.log('Clean.start_cleaning(): previous_state {}'.format(self.previous_state))
        self.log(kwargs)
        if self.previous_state != 'Clean':
            self.harmony_remote('remote.harmony_hub', 'on', activity='Clean')
        self.timer_start(self.timer, duration=10)

    def stop_cleaning(self, event_name, data, kwargs):
        self.harmony_remote('remote.harmony_hub', 'on', activity=self.previous_state)
        self.triggered = False
        self.log('Clean.stop_cleaning(): event_name {}, data {}'.format(event_name, data))
