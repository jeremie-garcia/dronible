import sys
from crazydrone import *
from riot import *
from PyQt5.QtCore import QCoreApplication

import time

app = QCoreApplication([])
riot_id = 0
print('creating riot')
riot = Riot(riot_id)
riot.start()
print('Finding available drones')

available = find_available_drones()
print('availables', str(available))

state = 0  # ground #1takeoff #2 flying

if len(available) > 0:
    drone = CrazyDrone(available[0][0])

    def process_acc(_x, _y, _z):
        global state
        print("state", state)
        if drone.motion_commander is not None:
            norm, x, y, z = riot.intensity(_x, _y, _z)

            if state == 0:
                if not drone.motion_commander._is_flying and norm > 100:
                    state = 1
                    drone.take_off()


            elif state == 1:
                height = drone.motion_commander._thread.get_height()
                if height > 0.2:
                    state = 2

            elif state == 2:
                up_speed = 0
                # range of norm is between 0 and 300
                v_min = -0.1
                v_max = 1
                up_speed = (norm / 300) * (v_max - v_min) + v_min
                up_speed = max(min(up_speed, v_max), v_min)
                print(up_speed)

                if drone.motion_commander._is_flying:
                    height = drone.motion_commander._thread.get_height()
                    if up_speed < 0 and height < 0.1:
                        state = 0
                        drone.land()

                    drone.process_motion(up_speed, 0, 0, 0)


    def start_control():
        print('connected to drones')
        app.aboutToQuit.connect(drone.land)
        riot.acc.connect(process_acc)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
sys.exit(app.exec_())
