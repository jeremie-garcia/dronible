#!/usr/bin/env python3
import logging
import sys
import time
import random

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.positioning.motion_commander import MotionCommander
from cflib.utils.multiranger import Multiranger

if len(sys.argv) > 1:
    URI = sys.argv[1]


def is_close(range):
    MIN_DISTANCE = 0.4  # m

    if range is None:
        return False
    else:
        return range < MIN_DISTANCE


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    available = cflib.crtp.scan_interfaces()

    if len(available) > 0:
        URI = available[0][0]
        cf = Crazyflie(rw_cache='./cache')

        with SyncCrazyflie(URI, cf=cf) as scf:
            with MotionCommander(scf, 0.7) as motion_commander:
                with Multiranger(scf) as multiranger:
                    keep_flying = True

                    state = 0
                    count = 0

                    while keep_flying:
                        _left = 0
                        _right = 0
                        _front = 0

                        if state == 0:
                            # close objects detection
                            if is_close(multiranger.right) and is_close(multiranger.left):
                                state = 1

                        elif state == 1:
                            # move towards selected direction until distance is 0.2
                            # throwing detection
                            if not is_close(multiranger.right) and not is_close(multiranger.left):
                                state = 2
                                _left = 0

                            # while in this state charge motion with oscillations
                            if multiranger.right < multiranger.left:
                                _left = 0.2
                            else:
                                _left = -0.2

                        elif state == 2:

                            # move forward until there is an obstacle then land
                            _front = 0.6
                            if is_close(multiranger.front):
                                _front = 0
                                keep_flying = False

                        print('state', state, 'motion', _front, _left)
                        motion_commander.start_linear_motion(
                            _front, _left, 0)

                        time.sleep(0.1)
