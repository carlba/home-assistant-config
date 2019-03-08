import inspect
import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime


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
        self.log(f'Clean.tracker(): entity {entity}, old {old}, new {new}, triggered {self.triggered}')
        if not self.triggered:
            if new == 'Clean':
                self.start_cleaning()
            elif old != 'Clean' and new == 'Away':
                self.log('Starting cleaning in 10 seconds')
                self.run_in(self.start_cleaning, 10)
        else:
            if old == 'Clean':
                self.log(f'{self.get_info()}: Cancelling Timer')
                self.timer_cancel(self.timer)
                self.triggered = False

    def start_cleaning(self, kwargs=None):
        self.triggered = True
        self.log(f'{self.get_info()}: previous_state {self.previous_state}')
        if self.previous_state != 'Clean':
            self.log(f'{self.get_info()}: previous_state{self.previous_state}')
            self.harmony_remote('remote.harmony_hub', 'turn_on', activity='Clean')
        self.timer_start(self.timer, duration=75*60)

    def stop_cleaning(self, event_name, data, kwargs):
        self.log(f'{self.get_info()}: event_name {event_name}, data {data}')
        self.harmony_remote('remote.harmony_hub', 'turn_on', activity=self.previous_state)
        self.triggered = False


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
        self.hours = self.args['hours'] or []
        self.turn_off_handle = None
        self.listen_state(self.handle_motion, self.binary_sensor)

    def get_current_hour_light_settings(self):
        for hour_range in self.hours:
            # TODO: Should compare datetimes instead of hour values
            range_match = hour_range['start'] <= datetime.now().hour <= hour_range['stop']
            self.log(f'{self.get_info()}: Matching: {hour_range["start"]} '
                     f'<= {datetime.now().hour} <= {hour_range["stop"]} = {range_match}')
            if range_match:
                return hour_range['brightness_pct'], hour_range.get('duration') or self.duration
        else:
            return None, self.duration

    def _turn_off(self, kwargs=None):
        motion_sensor_state = self.get_state(self.binary_sensor)
        if motion_sensor_state == 'off':
            self.turn_off(self.light)
            self.log(f'{self.get_info()}: Turned off {self.light}')

        self.turn_off_handle = None

    def handle_motion(self, entity, attribute, old, new, kwargs):
        self.log(f'{self.get_info()}: entity: {entity}, attribute: {attribute}, old: {old}, '
                 f'new {new}, kwargs: {repr(kwargs)}', level='INFO')

        current_hour_brightness, current_hour_duration = self.get_current_hour_light_settings()

        if (old == 'off' and new == 'on') and current_hour_brightness:
            self.log(f'{self.get_info()}: Trying to set entity {self.light} '
                     f'to {current_hour_brightness} brightness')
            self.turn_on(self.light,  brightness_pct=current_hour_brightness)
            self.log(f'{self.get_info()}: Turned on { self.light }')
            if self.turn_off_handle:
                self.turn_off_handle = self.cancel_timer(self.turn_off_handle)
            self.turn_off_handle = self.run_in(self._turn_off, current_hour_duration, entity_id=entity)

        if old == 'on' and new == 'off':
            if not self.turn_off_handle:
                self.turn_off(self.light)
                self.log(f'{self.get_info()}: Turned off {self.light}')


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


# noinspection PyAttributeOutsideInit
class TalkingTimer(ExtendedHass):

    def initialize(self):
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
        self.log(self.args)
        self.timer = self.args['timer']
        self.entity = self.args['entity']
        self.duration = self.args['duration']
        self.information = self.args['information']
        self.information_push = self.args['information_push']
        self.information_talk = self.args['information_talk']
        self.information_delay = self.args['information_delay']
        self.talk_hours = self.args['talk_hours']
        self.listen_state(self.handle_entity_state, self.entity)
        self.listen_event(self.stop_activity, event='timer.finished', entity_id=self.timer)

    def handle_entity_state(self, entity, attribute, old, new, kwargs):
        self.log(f'{self.get_info()}: entity: {entity}, attribute: {attribute}, old: {old}, '
                 f'new {new}, kwargs: {repr(kwargs)}', level='INFO')

        if old == 'off' and new == 'on':
            self.run_in(self.read_information, self.information_delay)
            self.timer_start(self.timer, duration=self.duration)
        elif old == 'on' and new == 'off':
            self.timer_cancel(self.timer)

    def stop_activity(self, event_name, data, kwargs):
        self.log(f'{self.get_info()}: Turning off {kwargs["entity_id"]} due to {event_name}')
        self.turn_off(self.entity)

    def read_information(self, _):
        if self.information_push:
            self.log(f'{self.get_info()}: Trying to push {self.information} to Pushover')
            self.call_service('notify/pushover',
                              message=self.information)

        if self.information_talk and (self.talk_hours[0] <= datetime.now().hour <= self.talk_hours[1]):
            self.log(f'{self.get_info()}: Trying to say {self.information}')
            self.call_service('tts/google_say',
                              entity_id='media_player.srsx77',
                              message=self.information)

