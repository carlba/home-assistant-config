import inspect
import appdaemon.plugins.hass.hassapi as hass


class ExtendedHass(hass.Hass):

    @staticmethod
    def get_info():
        target = inspect.stack()[1][0]
        target_method = inspect.stack()[1][3]

        if 'self' in target.f_locals:
            cls_name = target.f_locals['self'].__class__.__name__
            target_method = f'{cls_name}.{target_method}'

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

        self.call_service(f"remote/{state}", **rargs)


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class Clean(ExtendedHass):

    def initialize(self):
        self.log(f"{self.__class__.__name__}.initialize")
        self.timer = 'timer.clean'
        self.previous_state = None
        self.triggered = False
        self.harmony_remote_listener = self.listen_state(self.tracker,
                                                         entity='remote.harmony_hub',
                                                         attribute='current_activity')
        self.listen_event(self.stop_cleaning, event='timer.finished', entity_id=self.timer)

    def tracker(self, entity, attribute, old, new, kwargs):
        self.previous_state = old
        self.log(f'Clean.tracker(): entity {entity}, old {old}, new {new}')
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
        self.log(f'{self.get_info()}: previous_state {self.previous_state}')
        self.log(kwargs)
        if self.previous_state != 'Clean':
            self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Clean')
        self.timer_start(self.timer, duration=75*60)

    def stop_cleaning(self, event_name, data, kwargs):
        self.harmony_remote('remote.harmony_hub', 'turn_on', activity=self.previous_state)
        self.triggered = False
        self.log(f'{self.get_info()}: event_name {event_name}, data {data}')


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class HarmonyDeviceSwitch(ExtendedHass):

    def initialize(self):
        self.log(f"{self.__class__.__name__}.initialize")
        if not self.args['input_boolean'].startswith('input_boolean'):
            raise ValueError(f'The input_boolean has to be addressed with '
                             f'full path I.E input_boolean.{self.args["input_boolean"]}')

        self.input_boolean = self.args['input_boolean']
        self.on_command = self.args['on_command']
        self.off_command = self.args['off_command']
        self.input_boolean_listener = self.listen_state(self.on_input_boolean_change,
                                                        entity=self.input_boolean)

    def on_input_boolean_change(self, entity, attribute, old, new, kwargs):
        if old == 'off' and new == 'on':
            self.log(f'{self.get_info()}:Input boolean {entity} was turned on')

        elif old == 'on' and new == 'off':
            self.log(f'{self.get_info()}:Input boolean {entity} was turned off')


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class LogDeconzEvents(ExtendedHass):

    def initialize(self):
        self.log(f"{self.__class__.__name__}.initialize")
        self.listen_event(self.handle_event, "deconz_event")

    def handle_event(self, event_name, data, kwargs):
        self.log('{}: Event Name: {}, Data: {}, Kwargs: {}'.format(
            self.get_info(), event_name, data, repr(kwargs)))


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class ColorTemperature(ExtendedHass):

    def initialize(self):
        self.log(f"{self.__class__.__name__}.initialize")
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
        self.log(f"{self.__class__.__name__}.initialize")
        self.binary_sensor = self.args['binary_sensor']
        self.light = self.args['light']
        self.duration = self.args.get('duration') or 120
        self.turn_off_handle = None
        self.listen_state(self.handle_motion, self.binary_sensor)

    def _turn_off(self, kwargs=None):
        motion_sensor_state = self.get_state(self.binary_sensor)
        self.log(f'{self.get_info()}: The state of {kwargs["entity_id"]} is {motion_sensor_state}')
        if motion_sensor_state == 'off':
            self.turn_off(self.light)
            self.log(f'{self.get_info()}: Turned off {self.light}')

        self.turn_off_handle = None

    def handle_motion(self, entity, attribute, old, new, kwargs):
        self.log(f'{self.get_info()}: entity: {entity}, attribute: {attribute}, old: {old}, '
                 f'new {new}, kwargs: {repr(kwargs)}', level='INFO')

        if old == 'off' and new == 'on':
            self.turn_on(self.light)
            self.log('{}: Turned on {}'.format(self.get_info(), entity))
            if self.turn_off_handle:
                self.turn_off_handle = self.cancel_timer(self.turn_off_handle)
            self.turn_off_handle = self.run_in(self._turn_off, self.duration, entity_id=entity)

        if old == 'on' and new == 'off':
            self.log(f'{self.get_info()}: The state of the self.turn_off_handle is '
                     f'{self.turn_off_handle}')
            if not self.turn_off_handle:
                self.turn_off(self.light)


# noinspection PyAttributeOutsideInit
class RemoteControl(ExtendedHass):

    def initialize(self):
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
        self.id = self.args['id']
        self.entities = self.args['entities']
        if 'event' in self.args:
            self.listen_event(self.handle_event, self.args['event'])

    def handle_event(self, event_name, data, kwargs):
        if self.id in [data['id'], '*']:
            if data['event'] == 1002:
                self.log(f'{data["id"]} was turned on', level='INFO')
                for entity in self.entities:
                    self.turn_on(entity)

            elif data['event'] == 2002:
                self.log(f'{data["id"]} was turned off', level='INFO')
                for entity in self.entities:
                    self.turn_off(entity)

