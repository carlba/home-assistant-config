import pytest

from .apps import TradfriMotionSensor


@pytest.fixture
def tradfri_motion_sensor(given_that):
    given_that.passed_arg('binary_sensor').is_set_to('binary_sensor.hallway_motion_sensor')
    given_that.passed_arg('light').is_set_to('light.hallway_ceiling')
    given_that.passed_arg('duration').is_set_to(60)
    given_that.passed_arg('hours').is_set_to([{
        'start': 7,
        'stop': 18,
        'brightness_pct': 50,
        'duration': 60
    }])

    tradfri_motion_sensor = TradfriMotionSensor(None, None, None, None, None, None, None, None)
    tradfri_motion_sensor.initialize()
    given_that.mock_functions_are_cleared()
    return tradfri_motion_sensor


def test_movement_at_7(given_that, tradfri_motion_sensor, assert_that):
    given_that.state_of('binary_sensor.hallway_motion_sensor').is_set_to({'on': True})
    tradfri_motion_sensor.handle_motion('binary_sensor.hallway_motion_sensor', None, 'off', 'on', None)
    # tradfri_motion_sensor.test()
    assert_that('light.hallway_ceiling').was.turned_on(brightness_pct=50)


