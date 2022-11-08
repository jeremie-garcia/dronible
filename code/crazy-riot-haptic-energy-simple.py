from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout

from crazydrone import find_available_drones, CrazyDrone
from haptic import Haptic
from riot import Riot
import sys

"""
This examples demonstrates how to make the drone fly and use acceleration for vertical speed
The acceleration also controls the haptic feedback intensity
"""

app = QApplication([])

# create the Riot sensor - CHANGE THE ID
riot_id = 1  # Make it the correct one
riot = Riot(riot_id)

haptic = Haptic()

# look for the drone
available = find_available_drones()
print('availables crazyflies', str(available))

if len(available) > 0:
    drone = CrazyDrone(available[0][0])

    # create the widgets
    start_button = QPushButton("take off")
    stp_button = QPushButton("Land")
    widget = QWidget()
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.addWidget(start_button)
    layout.addWidget(stp_button)
    # connect button to the drone functions
    start_button.clicked.connect(drone.take_off)
    stp_button.clicked.connect(drone.land)
    # show the widget
    widget.show()

    # listen for batery messages and print
    drone.batteryValue.connect(lambda status: print('batt', status))
    drone.init()


    # listen to data from the riot
    def process_acceleration_intensity(_intensity, _x, _y, _z):

        # intensity is between O and 2 approx
        v_min = -0.1
        v_max = 1

        up_speed = (_intensity / 2) * (v_max - v_min) + v_min
        up_speed = max(min(up_speed, v_max), v_min)
        print("Up Speed from acceletation", up_speed)

        if drone.motion_commander is not None:  # test if the drone is ready to take orders :)
            # make the drone land if too low
            if drone.motion_commander._is_flying:
                height = drone.motion_commander._thread.get_height()
                print(height)
                if up_speed < 0 and height < 0.1:
                    state = 0
                    drone.land()
                else:
                    drone.process_motion(up_speed, 0, 0, 0)
                    haptic.set_continuous_level(_intensity/2)


    riot.acc_intensity.connect(process_acceleration_intensity)
    riot.start()
    haptic.start_continuous()
    haptic.stop_continuous()
    app.aboutToQuit.connect(riot.stop)
    app.aboutToQuit.connect(drone.stop)
    app.aboutToQuit.connect(haptic.stop_continuous)

else:
    print("No drone found")

sys.exit(app.exec_())

if drone:
    drone.stop()
