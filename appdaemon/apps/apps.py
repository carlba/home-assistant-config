import inspect
import json
from typing import Union, List, Dict

import appdaemon.plugins.hass.hassapi as hass
from datetime import datetime, time


class ExtendedHass(hass.Hass):
    @staticmethod
    def get_info(level_in_stack: int = 1):
        target = inspect.stack()[level_in_stack][0]
        target_method = inspect.stack()[level_in_stack][3]

        if 'self' in target.f_locals:
            cls_name = target.f_locals['self'].__class__.__name__
            target_method = f'{cls_name}.{target_method}'

        return target_method

    def log(self, msg: Union[str, dict, list], *args, **kwargs):
        message = json.dumps(msg) if isinstance(msg, dict) else msg
        super().log(f'{ExtendedHass.get_info(2)}: {message}', *args, **kwargs)

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
            raise TypeError("state must be 'on' or 'off'")

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
        self.log(
            f'Clean.tracker(): entity {entity}, old {old}, new {new}, triggered {self.triggered}')
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
        self.timer_start(self.timer, duration=75 * 60)

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
        self.log(f'Event Name: {event_name}, Data: {data}, Kwargs: {repr(kwargs)}')


# noinspection PyAttributeOutsideInit,PyUnusedLocal
class ColorTemperature(ExtendedHass):
    def initialize(self):
        self.log(f"{self.__class__.__name__}.initialize")
        self.daylight_sensor = self.args['sensor']
        self.listen_state(self.handle_state, self.daylight_sensor)
        self.log(f'Current daylight state: {self.get_state(self.daylight_sensor)}')

        # https://www.home-assistant.io/components/light/
        all_lights = self.get_state('group.all_lights', attribute='entity_id')

        self.set_state('sensor.default_light_settings',
                       state='on',
                       attributes={
                           'friendly_name': 'Default Light Settings',
                           'color_temp': '400'
                       })

    def handle_state(self, entity, attribute, old, new, kwargs):
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, new {new}, '
            f'kwargs: {repr(kwargs)}',
            level='INFO')


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
        self.test_hour = self.args.get('test_hour') or None

    def get_current_hour_light_settings(self):
        for hour_range in self.hours:
            # TODO: Should compare datetimes instead of hour values
            range_match = hour_range['start'] <= (self.test_hour
                                                  or datetime.now().hour) <= hour_range['stop']
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
            self.log(f'Turned off {self.light}')

        self.turn_off_handle = None

    def handle_motion(self, entity, attribute, old, new, kwargs):
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, new {new}, '
            f'kwargs: {repr(kwargs)}',
            level='INFO')

        current_hour_brightness, current_hour_duration = self.get_current_hour_light_settings()

        if (old == 'off' and new == 'on') and current_hour_brightness:
            self.log(f'Trying to set entity {self.light} to {current_hour_brightness} brightness')
            self.turn_on(self.light, brightness_pct=current_hour_brightness)
            self.log(f'Turned on {self.light}')
            if self.turn_off_handle:
                self.turn_off_handle = self.cancel_timer(self.turn_off_handle)
            self.turn_off_handle = self.run_in(self._turn_off,
                                               current_hour_duration,
                                               entity_id=entity)

        if old == 'on' and new == 'off':
            if not self.turn_off_handle:
                self.turn_off(self.light)
                self.log(f'Turned off {self.light}')


# noinspection PyAttributeOutsideInit
class RemoteControl(ExtendedHass):
    def initialize(self):
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
        self.id = self.args['id']
        self.listen_event(self.handle_event, self.args['event'], entity_id=self.id)
        self.type = self.args['type']
        self.event_map = {
            'ikea': {
                'on': 1002,
                'off': 2002
            },
            'hue': {
                'on': 1001,
                'off': 4001,
                'up': 2002,
                'down': 3002,
                'play': 1002,
                'pause': 4002
            }
        }

    def handle_event(self, event_name, data, kwargs):
        self.id = self.args['id']
        self.log(data)
        if self.id in [data['id'], '*']:
            if data['event'] == self.event_map[self.type]['on']:
                self.set_state(f'sensor.{data["id"]}', state='on')
                self.handle_turn_on(event_name, data, kwargs)

            elif data['event'] == self.event_map[self.type]['off']:
                self.set_state(f'sensor.{data["id"]}', state='off')
                self.handle_turn_off(event_name, data, kwargs)

            elif self.event_map[self.type].get('up') and data['event'] == self.event_map[
                    self.type]['up']:
                self.handle_up(event_name, data, kwargs)

            elif self.event_map[self.type].get('down') and data['event'] == self.event_map[
                    self.type]['down']:
                self.handle_down(event_name, data, kwargs)

            elif self.event_map[self.type].get('play') and data['event'] == self.event_map[
                    self.type]['play']:
                self.handle_play(event_name, data, kwargs)

            elif self.event_map[self.type].get('pause') and data['event'] == self.event_map[
                    self.type]['pause']:
                self.handle_pause(event_name, data, kwargs)

    def handle_turn_on(self, event_name, data, kwargs):
        self.log(f'{data["id"]} was turned on', level='INFO')

    def handle_turn_off(self, event_name, data, kwargs):
        self.log(f'{data["id"]} was turned off', level='INFO')

    def handle_up(self, event_name, data, kwargs):
        self.log(f'{data["id"]} increased state by one', level='INFO')

    def handle_down(self, event_name, data, kwargs):
        self.log(f'{data["id"]} decreased state by one', level='INFO')

    def handle_play(self, event_name, data, kwargs):
        self.log(f'{data["id"]} started playing', level='INFO')

    def handle_pause(self, event_name, data, kwargs):
        self.log(f'{data["id"]} paused playback', level='INFO')


# noinspection PyAttributeOutsideInit
class RemoteControlAction(RemoteControl):
    def initialize(self):
        super().initialize()
        self.entities = self.args['entities']

    def handle_turn_on(self, event_name, data, kwargs):
        super().handle_turn_on(event_name, data, kwargs)
        for entity in self.entities:
            self.turn_on(entity)
        self.log(f'{self.entities} was turned off', level='INFO')

    def handle_turn_off(self, event_name, data, kwargs):
        super().handle_turn_off(event_name, data, kwargs)
        for entity in self.entities:
            self.turn_off(entity)
        self.log(f'{self.entities} was turned on', level='INFO')


# noinspection PyAttributeOutsideInit
class RemoteControlService(RemoteControl):
    def initialize(self):
        super().initialize()
        self.entities: List[str] = self.args.get('entities')
        self.service_calls: Dict[List[Dict[str,
                                           Union[str,
                                                 Dict[str,
                                                      Union[str,
                                                            int]]]]]] = self.args['service_calls']

    def get_service_calls_for_event(self, service_calls, event: str):
        new_service_calls: List[dict] = []

        for call in service_calls[event]:
            entity_id = call['data'].get('entity_id')
            if not entity_id:
                if not self.entities:
                    raise TypeError('Entities needs to be provided in YAML')
                for entity in self.entities:
                    call['data']['entity_id'] = entity
                    service_call = {
                        'args': [call['service'].replace('.', '/')],
                        'kwargs': call['data']
                    }
                    new_service_calls.append(service_call)
            else:
                service_call = {'args': [call['service'].replace('.', '/')], 'kwargs': call['data']}
                new_service_calls.append(service_call)
        return new_service_calls

    def handle_turn_on(self, event_name, data, kwargs):
        super().handle_turn_on(event_name, data, kwargs)
        self.log(self.service_calls, level='INFO')
        new_service_calls = self.get_service_calls_for_event(self.service_calls, 'on')
        for service_call in new_service_calls:
            self.call_service(*service_call['args'], **service_call['kwargs'])

    def handle_turn_off(self, event_name, data, kwargs):
        super().handle_turn_off(event_name, data, kwargs)
        new_service_calls = self.get_service_calls_for_event(self.service_calls, 'off')
        for service_call in new_service_calls:
            self.log(
                f'Trying to call service with args:{service_call["args"]} kwargs:{service_call["kwargs"]}'
            )
            self.call_service(*service_call['args'], **service_call['kwargs'])


# noinspection PyAttributeOutsideInit
class MediaController(RemoteControl):
    def initialize(self):
        super().initialize()
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
        self.tv = self.args['tv']
        self.speaker = self.args['speaker']
        self.listen_state(self.handle_tv_state, self.tv)
        self.listen_state(self.handle_speaker_state, self.speaker)

        self.current_state = {
            'tv': {
                self.tv: self.get_state(self.tv) or 'unknown'
            },
            'speaker': {
                self.speaker: self.get_state(self.speaker) or 'unknown'
            }
        }

    def handle_play(self, event_name, data, kwargs):
        super().handle_turn_on(event_name, data, kwargs)
        self.log(f'turn on', level='INFO')
        if self.current_state['tv'][self.tv] == 'paused':
            self.call_service('media_player/media_play', entity_id=self.tv)
        elif self.current_state['speaker'][self.speaker] == 'paused':
            self.call_service('media_player/media_play', entity_id=self.speaker)

    def handle_pause(self, event_name, data, kwargs):
        super().handle_turn_off(event_name, data, kwargs)
        self.log(f'turn off', level='INFO')
        if self.current_state['tv'][self.tv] == 'playing':
            self.call_service('media_player/media_pause', entity_id=self.tv)
        elif self.current_state['speaker'][self.speaker] == 'playing':
            self.call_service('media_player/media_pause', entity_id=self.speaker)

    def handle_tv_state(self, entity, attribute, old, new, kwargs):
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, '
            f'new {new}, kwargs: {repr(kwargs)}',
            level='INFO')
        self.current_state['tv'][entity] = new
        self.log(json.dumps(self.current_state))

    def handle_speaker_state(self, entity, attribute, old, new, kwargs):
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, '
            f'new {new}, kwargs: {repr(kwargs)}',
            level='INFO')
        self.current_state['speaker'][entity] = new
        self.log(self.current_state)


# noinspection PyAttributeOutsideInit
class MediaControllerVolume(MediaController):
    # https://www.home-assistant.io/integrations/androidtv/

    def initialize(self):
        super().initialize()
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')

    def launch_android_tv_app(self, entity_id, app_id: str):
        self.call_service('media_player/select_source', entity_id=entity_id, source=app_id)

    def send_android_tv_key(self, entity_id, key: str):
        self.call_service('androidtv/adb_command', entity_id=entity_id, command=key)

    def handle_up(self, event_name, data, kwargs):
        super().handle_up(event_name, data, kwargs)
        self.log(f'{data["id"]} increased volume', level='INFO')
        self.log(f'{self.get_state(self.speaker, attribute="volume_level")}')

        if self.current_state['tv'][self.tv] == 'playing':
            volume_level = self.get_state(self.tv, attribute="volume_level")
            self.call_service('media_player/volume_set',
                              volume_level=volume_level + 0.1,
                              entity_id=self.tv)
        elif self.current_state['speaker'][self.speaker] == 'playing':
            volume_level = self.get_state(self.speaker, attribute="volume_level")
            self.call_service('media_player/volume_set',
                              volume_level=volume_level + 0.01,
                              entity_id=self.speaker)

    def handle_down(self, event_name, data, kwargs):
        super().handle_down(event_name, data, kwargs)
        self.log(f'{data["id"]} decreased volume', level='INFO')
        self.log(f'{self.get_state(self.speaker, attribute="volume_level")}')

        if self.current_state['tv'][self.tv] == 'playing':
            volume_level = self.get_state(self.tv, attribute="volume_level")
            new_volume_level = volume_level - 0.1 if volume_level > 0.1 else 0
            self.call_service('media_player/volume_set',
                              volume_level=new_volume_level,
                              entity_id=self.tv)
        elif self.current_state['speaker'][self.speaker] == 'playing':
            volume_level = self.get_state(self.speaker, attribute="volume_level")
            new_volume_level = volume_level - 0.01 if volume_level > 0.01 else 0
            self.call_service('media_player/volume_set',
                              volume_level=new_volume_level,
                              entity_id=self.speaker)

    def handle_turn_on(self, event_name, data, kwargs):
        super().handle_turn_on(event_name, data, kwargs)
        if self.get_state(self.tv) == 'off':
            self.turn_on(self.tv)

    def handle_turn_off(self, event_name, data, kwargs):
        super().handle_turn_off(event_name, data, kwargs)
        self.log(f'state: {self.get_state(self.tv)}')
        if self.get_state(self.tv) != 'off':
            self.turn_off(self.tv)


# noinspection PyAttributeOutsideInit
class TalkingTimer(ExtendedHass):
    def initialize(self):
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
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
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, new {new}, '
            f'kwargs: {repr(kwargs)}',
            level='INFO')

        if old == 'off' and new == 'on':
            self.run_in(self.read_information, self.information_delay)
            self.timer_start(self.timer, duration=self.duration)
        elif old == 'on' and new == 'off':
            self.timer_cancel(self.timer)

    def stop_activity(self, event_name, data, kwargs):
        self.log(f'Turning off {kwargs["entity_id"]} due to {event_name}')
        self.turn_off(self.entity)

    def read_information(self, _):
        if self.information_push:
            self.log(f'Trying to push {self.information} to Pushover')
            self.call_service('notify/pushover', message=self.information)

        if self.information_talk and (self.talk_hours[0] <= datetime.now().hour <=
                                      self.talk_hours[1]):
            self.log(f'Trying to say {self.information}')
            self.call_service('notify/gassistant', message=self.information)


class TimeRange:
    def __init__(self, data, time_format='%H:%M:%S'):
        self.time_format = time_format
        self.time_range = {
            "start": self.time_to_timestring(data['start']),
            "stop": self.time_to_timestring(data['stop'])
        }
        self.entities = data['entities']
        self.name = data.get('name')

    def __repr__(self):
        return f'{self.format_name()} {self.time_range["start"]} - {self.time_range["stop"]}'

    def format_name(self):
        return f'{self.name if self.name else "NoName" + ":"}'

    def time_to_timestring(self, time_string):
        return datetime.strptime(time_string, self.time_format).time()

    def match(self, time: time):
        return self.time_range['start'] < time < self.time_range['stop']

    def match_now(self):
        self.match(datetime.now().time())


# noinspection PyAttributeOutsideInit
class TimeBasedPersonTracker(ExtendedHass):
    def initialize(self):
        self.log(f'{self.__class__.__name__}.initialize', level='INFO')
        self.group = self.args['group']

        self.time_ranges = [TimeRange(time_range) for time_range in self.args['time_ranges']]
        self.log(self.time_ranges)
        self.listen_state(self.handle_group_state, self.group)

    @property
    def all_lights(self):
        return self.get_state('light').keys()

    def handle_group_state(self, entity, attribute, old, new, kwargs):
        self.log(
            f'entity: {entity}, attribute: {attribute}, old: {old}, new {new}, '
            f'kwargs: {repr(kwargs)}',
            level='INFO')

        for time_range in self.time_ranges:
            if time_range.match_now():
                for entity in time_range.entities:
                    self.turn_on(entity_id=entity)
