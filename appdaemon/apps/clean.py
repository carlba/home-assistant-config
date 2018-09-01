import appdaemon.plugins.hass.hassapi as hass


class Clean(hass.Hass):

    @hass.hass_check
    def timer_start(self, entity_id, duration=None, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        if kwargs == {}:
            rargs = {"entity_id": entity_id}
        else:
            rargs = kwargs
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
        if kwargs == {}:
            rargs = {"entity_id": entity_id}
        else:
            rargs = kwargs
            rargs["entity_id"] = entity_id
            rargs["state"] = state
            rargs["activity"] = activity

        self.call_service("remote/turn_{}".format(state), **rargs)

    def initialize(self):
        self.timer = 'timer.clean'
        # self.listen_state(self.tracker, entity='switch.harmony_hub_home')
        # self.listen_state(self.tracker, entity='switch.harmony_hub_clean')
        self.listen_state(self.stop_cleaning, entity='switch.harmony_hub_clean')

    def tracker(self, entity, attribute, old, new, kwargs):
        self.log('tracker')
        self.log('new {}'.format(new))

        if new == 'on':
            if entity == 'switch.harmony_hub_home':
                self.log('test')
                self.run_in(self.start_cleaning, 5)
            elif entity is 'switch.harmony_hub_clean':
                self.start_cleaning()

    def start_cleaning(self, kwargs=None):
        self.log('Start Cleaning')
        self.timer_start(self.timer, duration=2)
        self.switch_on('switch.harmony_hub_clean')

    def stop_cleaning(self, entity, attribute, old, new, kwargs):
        self.harmony_remote('remote.harmony_hub', 'on', activity='Home')

