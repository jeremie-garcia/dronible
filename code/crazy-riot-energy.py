import crazydrone
from riot import Riot
from PyQt5.QtCore import QCoreApplication
import sys

"""
This examples uses the acceleration intensity to control the takeoff and vertical speed of the drone 
"""

app = QCoreApplication([])
riot_id = 0
print('creating riot')
riot = Riot(riot_id)
riot.start()
print('Finding available drones')

available = crazydrone.find_available_drones()
print('availables', str(available))

state = 0  # ground #1takeoff #2 flying

if len(available) > 0:
    drone = crazydrone.CrazyDrone(available[0][0])


    def process_acceleration_intensity(_intensity, _x,_y,_z):
        global state
        print("state", state)
        if drone.motion_commander is not None:

            if state == 0:
                if not drone.motion_commander._is_flying and _intensity > 1:
                    state = 1
                    drone.take_off()

            elif state == 1:
                height = drone.motion_commander._thread.get_height()
                if height > 0.2:
                    state = 2

            elif state == 2:
                up_speed = 0
                # range of norm is between 0 and 5
                v_min = -0.1
                v_max = 1
                up_speed = (_intensity / 2) * (v_max - v_min) + v_min
                up_speed = max(min(up_speed, v_max), v_min)
                print(up_speed)

                if drone.motion_commander._is_flying:
                    height = drone.motion_commander._thread.get_height()
                    if up_speed < 0 and height < 0.1:
                        state = 0
                        drone.land()

                    drone.process_motion(up_speed, 0, 0, 0)


    def start_control(status):
        if status == "on":
            print('connected to drones')
            riot.acc.connect(process_acceleration_intensity)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
app.aboutToQuit.connect(drone.land)
sys.exit(app.exec_())
