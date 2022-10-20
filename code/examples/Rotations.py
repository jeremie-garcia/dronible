import sys
from crazydrone import *
from PyQt5.QtCore import QCoreApplication

import time

from dronibles.riot import Riot, spin

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

    def process_gyro(_x, _y, _z):
        global state

        if drone.motion_commander is not None:
            x, y, z = riot.spin_filtered(_x, _y, _z)
            norm = spin(_x, _y, _z)
            print("state", state, "norm", norm)
            if state == 0:
                if not drone.motion_commander._is_flying and abs(z) > 0.5:
                    state = 1
                    drone.take_off()


            elif state == 1:
                height = drone.motion_commander._thread.get_height()
                if height > 0.2:
                    state = 2

            elif state == 2:
                if abs(z) < 0.01:
                    z = 0
                up_speed = z / 10
                print(up_speed)

                if drone.motion_commander._is_flying:
                    height = drone.motion_commander._thread.get_height()
                    if up_speed >0 and height > 2 :
                        up_speed = 0
                    elif up_speed < 0 and height < 0.1:
                        state = 0
                        drone.land()
                        state = 0
                    drone.process_motion(up_speed, 0, 0, 0)

    def start_control():
        print('connected to drones')
        app.aboutToQuit.connect(drone.land)
        riot.gyro.connect(process_gyro)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
sys.exit(app.exec_())
