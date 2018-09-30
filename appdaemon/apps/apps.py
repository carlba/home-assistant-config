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
    def timer_cancel(self, entity_id, **kwargs):
        self._check_entity(self._get_namespace(**kwargs), entity_id)
        rargs = kwargs or {}
        rargs["entity_id"] = entity_id
        self.call_service("timer/cancel", **rargs)

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
        if state not in ['turn_on', 'turn_off']:
            raise(TypeError, "state must be 'on' or 'off'")

        rargs = kwargs or {}
        rargs["entity_id"] = entity_id
        rargs["activity"] = activity

        self.call_service("remote/{}".format(state), **rargs)


# noinspection PyAttributeOutsideInit,PyUnusedLocal
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
            if old == 'Clean':
                self.timer_cancel(self.timer)
                self.triggered = False

    def start_cleaning(self, kwargs=None):
        self.triggered = True
        self.log('Clean.start_cleaning(): previous_state {}'.format(self.previous_state))
        self.log(kwargs)
        if self.previous_state != 'Clean':
            self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Clean')
        self.timer_start(self.timer, duration=75*60)

    def stop_cleaning(self, event_name, data, kwargs):
        self.harmony_remote('remote.harmony_hub', 'turn_on', activity=self.previous_state)
        self.triggered = False
        self.log('Clean.stop_cleaning(): event_name {}, data {}'.format(event_name, data))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class Scenes(ExtendedHass):

    def initialize(self):

        for item in ['movie']:
            self.harmony_remote_listener = self.listen_state(getattr(self, 'on_{}'.format(item)),
                                                             entity='input_boolean.{}'.format(item))

        self.scene_booleans = ['input_boolean.movie']
        self.log('self.scene_booleans: {}'.format(repr(self.scene_booleans)))

    def on_movie(self, entity, attribute, old, new, kwargs):
        if old == 'off' and new == 'on':
            self.log('Scenes.on_movie(): Input boolean movie was turned on')
            self.turn_off('group.lights')

            # self.call_service('remote/send_command', entity_id='remote.harmony_hub',
            #                   device='57605309', command='Sleep')
            # self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Shield')

        elif old == 'on' and new == 'off':
            self.log('Scenes.on_movie(): Input boolean movie was turned off')
            #self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Home')
            pass




