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
mean = 10000
start_landing_time = 0

if len(available) > 0:
    drone = CrazyDrone(available[0][0])

    def process_analog(_a1, _a2):
        global state
        global mean
        global start_landing_time
        mean = (_a1 + mean) / 2
        print("state", state, "mean", mean)
        if drone.motion_commander is not None:

            if state == 0:
                if not drone.motion_commander._is_flying and mean < 1800:
                    state = 1
                    drone.take_off()


            elif state == 1:
                if mean > 2000:
                    state = 2
                    if drone.motion_commander._is_flying:
                        drone.land()
                        start_landing_time = time.time()


            #wait 3seconds for landing

            elif state == 2:
                delta = time.time() - start_landing_time
                print(delta)
                if delta > 5:
                    state = 0


    def start_control():
        print('connected to drones')
        app.aboutToQuit.connect(drone.land)
        riot.analog.connect(process_analog)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
sys.exit(app.exec_())
