from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout

from crazydrone import find_available_drones, CrazyDrone
from riot import Riot
import sys

"""
This examples demonstrates how to make the drone rotates if the sensor is thrown into the air
"""

app = QApplication([])

#create the Riot sensor - CHANGE THE ID
riot_id = 1 #Make it the correct one
riot = Riot(riot_id)

#look for the drone
available = find_available_drones()
print('availables crazyflies', str(available))

if len(available) > 0:
    drone = CrazyDrone(available[0][0])

    #create the widgets
    start_button = QPushButton("take off")
    stp_button = QPushButton("Land")
    widget = QWidget()
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.addWidget(start_button)
    layout.addWidget(stp_button)
    #connect button to the drone functions
    start_button.clicked.connect(drone.take_off)
    stp_button.clicked.connect(drone.land)
    #show the widget
    widget.show()

    #listen for batery messages and print
    drone.batteryValue.connect(lambda status: print('batt', status))
    drone.init()


    #listen to data from the riot
    def process_freefall(_acc, _falling, _duration):
        v_min = 0
        v_max = 1
        angular_speed = (_falling / 2) * (v_max - v_min) + v_min
        angular_speed = max(min(angular_speed, v_max), v_min)
        print(angular_speed)

        if drone.motion_commander is not None: #test if the drone is ready to take orders :)
            #intensity is between O and 2 approx


            if drone.motion_commander._is_flying:
                    drone.process_motion(0, angular_speed, 0, 0)

    riot.freefall.connect(process_freefall)
    riot.start()
    app.aboutToQuit.connect(riot.stop)
    app.aboutToQuit.connect(drone.stop)

else:
    print("No drone found")



sys.exit(app.exec_())

if drone:
    drone.stop()

