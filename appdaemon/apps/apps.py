import inspect
import appdaemon.plugins.hass.hassapi as hass


class ExtendedHass(hass.Hass):

    @staticmethod
    def get_info():
        target = inspect.stack()[1][0]
        target_method = inspect.stack()[1][3]

        if 'self' in target.f_locals:
            cls_name = target.f_locals['self'].__class__.__name__
            target_method = "{}.{}".format(cls_name, target_method)

        return target_method

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
        self.log('{}: previous_state {}'.format(self.get_info(), self.previous_state))
        self.log(kwargs)
        if self.previous_state != 'Clean':
            self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Clean')
        self.timer_start(self.timer, duration=75*60)

    def stop_cleaning(self, event_name, data, kwargs):
        self.harmony_remote('remote.harmony_hub', 'turn_on', activity=self.previous_state)
        self.triggered = False
        self.log('{}: event_name {}, data {}'.format(self.get_info(), event_name, data))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class HarmonyDeviceSwitch(ExtendedHass):

    def initialize(self):

        if not self.args['input_boolean'].startswith('input_boolean'):
            raise ValueError('The input_boolean has to be addressed with '
                             'full path I.E input_boolean.{}'.format(self.args['input_boolean']))

        self.input_boolean = self.args['input_boolean']
        self.on_command = self.args['on_command']
        self.off_command = self.args['off_command']
        self.input_boolean_listener = self.listen_state(self.on_input_boolean_change,
                                                        entity=self.input_boolean)

    def on_input_boolean_change(self, entity, attribute, old, new, kwargs):
        if old == 'off' and new == 'on':
            self.log('{}:Input boolean {} was turned on'.format(self.get_info(), entity))

        elif old == 'on' and new == 'off':
            self.log('{}:Input boolean {} was turned off'.format(self.get_info(), entity))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class LogDeconzEvents(ExtendedHass):

    def initialize(self):
        self.log("LogDeconzEvents.initialize")
        self.listen_event(self.handle_event, "deconz_event")

    def handle_event(self, event_name, data, kwargs):
        self.log('{}: Event Name: {}, Data: {}, Kwargs: {}'.format(
            self.get_info(), event_name, data, repr(kwargs)))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class ColorTemperature(ExtendedHass):

    def initialize(self):
        self.log("{}.initialize".format(self.__class__.__name__))
        self.daylight_sensor = self.args['sensor']
        self.listen_state(self.handle_state, self.daylight_sensor)
        self.log('{}: Current daylight state:{}'.format(self.get_info(),
                                                        self.get_state(self.daylight_sensor)))

        # https://www.home-assistant.io/components/light/
        all_lights = self.get_state('group.all_lights', attribute='entity_id')

        self.set_state('sensor.default_light_settings', state='on',
                       attributes={'friendly_name': 'Default Light Settings', 'color_temp': '400'})

        self.log('{}: {}'.format(self.get_info(), all_lights))

    def handle_state(self, entity, attribute, old, new, kwargs):
        self.log('{}: entity: {}, attribute: {}, old: {}, new {}, kwargs: {}'.format(
            self.get_info(), entity, attribute, old, new, repr(kwargs)), level='INFO')


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class TradfriMotionSensor(ExtendedHass):

    def initialize(self):
        self.log("{}.initialize".format(self.__class__.__name__))
        self.binary_sensor = self.args['binary_sensor']
        self.light = self.args['light']
        self.listen_state(self.handle_motion, self.binary_sensor)

    def handle_motion(self, entity, attribute, old, new, kwargs):
        if old == 'off' and new == 'on':
            self.turn_on(self.light)
            self.log('{}: Turned on {}'.format(self.get_info(), entity))
        if old == 'on' and new == 'off':
            self.turn_off(self.light)
            self.log('{}: Turned off {}'.format(self.get_info(), entity))
        else:
            self.log('{}: Unhandled event'.format(self.get_info()))

        self.log('{}: entity: {}, attribute: {}, old: {}, new {}, kwargs: {}'.format(
            self.get_info(), entity, attribute, old, new, repr(kwargs)), level='DEBUG')



