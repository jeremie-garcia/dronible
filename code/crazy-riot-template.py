from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout

from drone.crazydrone import find_available_drones, CrazyDrone
from riot import Riot
import sys

"""
This examples demonstrates how to make the drone fly and display senor values
"""

app = QApplication([])

#create the Riot sensor - CHANGE THE ID
riot_id = 3 #Make it the correct one
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
    def process_acc(_x,_y,_z):
        print("Acceleration", _x,_y,_z)

    riot.acc.connect(process_acc)
    riot.start()
    app.aboutToQuit.connect(riot.stop)
    app.aboutToQuit.connect(drone.stop)

else:
    print("No drone found")



sys.exit(app.exec_())

if drone:
    drone.stop()

