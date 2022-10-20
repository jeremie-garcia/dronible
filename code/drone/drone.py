from PyQt5.QtCore import pyqtSignal, QObject

ANTI_COLLISION_MIN_DIST = 0.20  # meters
ANTI_COLLISION_DISTANCE = 1  # meters


def find_available_drones():
    raise NotImplementedError


class Drone(QObject):
    connection = pyqtSignal(str) #value: 'on', 'off'
    batteryValue = pyqtSignal(float) #value: 'between 0 and 100'
    is_flying_signal = pyqtSignal(bool) #True or False


    def __init__(self):
        super().__init__()

        # maximum speeds
        self.max_vert_speed = 1
        self.max_horiz_speed = 1
        self.max_rotation_speed = 90
        self.logger = None

    def init(self):
        raise NotImplementedError

    def take_off(self):
        raise NotImplementedError

    def land(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def is_flying(self):
        raise NotImplementedError

    def set_max_vertical_speed(self, _max):
        self.max_vert_speed = _max

    def set_max_horizontal_speed(self, _max):
        self.max_horiz_speed = _max

    def set_max_rotation_speed(self, _max):
        self.max_rotation_speed = _max

    def process_motion(self, _up, _rotate, _front, _right):
        raise NotImplementedError
