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


def is_close(range, dist=0.6):
    if range is None:
        return False
    else:
        return range < dist


if __name__ == '__main__':
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)
    available = cflib.crtp.scan_interfaces()
    print(available)

    if len(available) > 0:
        URI = available[0][0]
        cf = Crazyflie(rw_cache='./cache')

        with SyncCrazyflie(URI, cf=cf) as scf:
            with MotionCommander(scf, 1.2) as motion_commander:
                with Multiranger(scf) as multiranger:
                    keep_flying = True

                    state = 0
                    count = 0
                    _range = 2

                    while keep_flying:
                        _left = 0
                        _choice = ""

                        if state == 0:
                            # close objects detection
                            print('right', multiranger.right, "left", multiranger.left)
                            if is_close(multiranger.right, dist=0.6) and is_close(multiranger.left, dist=0.6):
                                state = 1
                                # choose a direction
                                _choice = random.choice(['right', 'left'])
                                print('choice', _choice)

                        # oscillate a moment before moving toward the chosen item
                        elif state == 1:
                            if count % 10 < 5:
                                _left = 0.2
                            else:
                                _left = -0.2

                            count = count + 1

                            if count > 40:
                                state = 2

                        # move towards selected direction until distance is 0.2
                        elif state == 2:
                            # throwing detection
                            if _choice == 'right':
                                _range = multiranger.right
                                _left = -0.2
                            else:
                                _range = multiranger.left
                                _left = 0.2

                            if is_close(_range, 0.15):
                                _left = 0
                                state = 0
                                keep_flying = False

                        print('state', state, 'motion', _left, 'range', _range)
                        motion_commander.start_linear_motion(0, _left, 0)

                        time.sleep(0.1)