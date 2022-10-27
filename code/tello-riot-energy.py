from drone.tello import TelloDrone
from riot import Riot
from PyQt5.QtCore import QCoreApplication
import sys

"""
This examples uses the acceleration intensity to control the takeoff and vertical speed of the drone 
"""

app = QCoreApplication([])
riot_id = 3
print('creating riot')
riot = Riot(riot_id)
riot.start()

state = 0
# ground #1takeoff #2 flying

drone = TelloDrone()


def process_acc(_x, _y, _z):
    global state
    if drone is not None:
        norm, x, y, z = riot.acc_intensity(_x, _y, _z)
        print("State", state, "Acc", norm, "flying?", drone.is_flying(), "height", drone.height())
        if state == 0:
            if not drone.is_flying() and norm > 1:
                state = 1
                drone.take_off()

        elif state == 1:
            if drone.height() > 0.5:
                state = 2

        elif state == 2:
            up_speed = 0
            # range of norm is between 0 and 300
            v_min = -0.1
            v_max = 1
            up_speed = (norm / 300) * (v_max - v_min) + v_min
            up_speed = max(min(up_speed, v_max), v_min)
            print(up_speed)

            if drone.is_flying():
                if up_speed < 0 and drone.height() < 0.1:
                    state = 0
                    drone.land()
                else:
                    pass
                    #drone.process_motion(up_speed, 0, 0, 0)


def start_control(status):
    print(status)
    if status =="on":
        print('connected to the drone- start processing sensor data')
        riot.acc.connect(process_acc)
    else:
        print("Not connected to the drone, check the WIFI")


drone.connection.connect(start_control)
drone.init()
app.aboutToQuit.connect(riot.stop)
app.aboutToQuit.connect(drone.land)
sys.exit(app.exec_())
