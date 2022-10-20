import os
import sys

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger

from drone.drone import *

cflib.crtp.init_drivers(enable_debug_driver=False)


def find_available_drones():
    return cflib.crtp.scan_interfaces()


class CrazyDrone(Drone):

    def __init__(self, link_uri):
        super().__init__()

        cache = "./cache"
        if getattr(sys, 'frozen', False):
            cache = sys._MEIPASS + os.path.sep + "cache"

        self._cf = Crazyflie(rw_cache=cache)
        self.motion_commander = None
        self.multiranger = None

        # maximum speeds
        self.max_vert_speed = 1
        self.max_horiz_speed = 1
        self.max_rotation_speed = 90

        self.logger = None

        # Connect some callbacks from the Crazyflie API
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        print('Connecting to %s' % link_uri)

        # Try to connect to the Crazyflie
        self._cf.open_link(link_uri)

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        print('Connected to %s' % link_uri)

        self.connection.emit("progress")

        # The definition of the logconfig can be made before connecting
        self.logger = LogConfig("Battery", 1000)  # delay
        self.logger.add_variable("pm.vbat", "float")

        try:
            self._cf.log.add_config(self.logger)
            self.logger.data_received_cb.add_callback(lambda e, f, g: self.batteryValue.emit(float(f['pm.vbat'])))
            # self.logger.error_cb.add_callback(lambda: print('error'))
            self.logger.start()
        except KeyError as e:
            print(e)

        self.connection.emit("on")
        self.motion_commander = MotionCommander(self._cf, 0.5)
        self.multiranger = Multiranger(self._cf, rate_ms=50)
        self.multiranger.start()

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the speficied address)"""
        print('Connection to %s failed: %s' % (link_uri, msg))
        self.is_connected = False
        self.connection.emit("off")

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print('Connection to %s lost: %s' % (link_uri, msg))
        self.connection.emit("off")

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print('Disconnected from %s' % link_uri)
        self.is_connected = False
        self.connection.emit("off")

    def take_off(self):
        if self._cf.is_connected() and self.motion_commander and not self.motion_commander._is_flying:
            self.motion_commander.take_off()
            self.is_flying_signal.emit(True)

    def land(self):
        if self._cf.is_connected() and self.motion_commander and self.motion_commander._is_flying:
            self.motion_commander.land()
            self.is_flying_signal.emit(False)

    def stop(self):
        if not (self.logger is None):
            self.logger.stop()
        if self.motion_commander:
            self.motion_commander.land()
        if self.multiranger:
            self.multiranger.stop()
        self._cf.close_link()

    def is_flying(self):
        if self._cf.is_connected() and self.motion_commander:
            return self.motion_commander._is_flying

        return False

    def process_motion(self, _up, _rotate, _front, _right):
        if self.motion_commander:

            # WARNING FOR CRAZYFLY
            # positive X is forward, # positive Y is left # positive Z is up

            velocity_z = _up * self.max_vert_speed
            velocity_yaw = _rotate * self.max_rotation_speed
            velocity_x = _front * self.max_horiz_speed
            velocity_y = - _right * self.max_horiz_speed
            # print("PRE", velocity_x, velocity_y, velocity_z, velocity_yaw)

            # protect against collision by reducing speed depending on distance
            ranger = self.multiranger

            if ranger.front and ranger.front < ANTI_COLLISION_DISTANCE and velocity_x > 0:
                velocity_x = velocity_x * (ranger.front - ANTI_COLLISION_MIN_DIST) / ANTI_COLLISION_DISTANCE
                velocity_x = max(0, velocity_x)

            if ranger.back and ranger.back < ANTI_COLLISION_DISTANCE and velocity_x < 0:
                velocity_x = velocity_x * (ranger.back - ANTI_COLLISION_MIN_DIST) / ANTI_COLLISION_DISTANCE
                velocity_x = min(0, velocity_x)

            if ranger.left and ranger.left < ANTI_COLLISION_DISTANCE and velocity_y > 0:
                velocity_y = velocity_y * (ranger.left - ANTI_COLLISION_MIN_DIST) / ANTI_COLLISION_DISTANCE
                velocity_y = max(0, velocity_y)

            if ranger.right and ranger.right < ANTI_COLLISION_DISTANCE and velocity_y < 0:
                velocity_y = velocity_y * (ranger.left - ANTI_COLLISION_MIN_DIST) / ANTI_COLLISION_DISTANCE
                velocity_y = min(0, velocity_y)

            if ranger.up and ranger.up < ANTI_COLLISION_DISTANCE and velocity_z > 0:
                velocity_z = velocity_z * (ranger.up - ANTI_COLLISION_MIN_DIST) / ANTI_COLLISION_DISTANCE
                velocity_z = max(0, velocity_z)

            # print("POST", velocity_x, velocity_y, velocity_z, velocity_yaw)
            if self.motion_commander._is_flying:
                self.motion_commander._set_vel_setpoint(velocity_x, velocity_y, velocity_z, velocity_yaw)
