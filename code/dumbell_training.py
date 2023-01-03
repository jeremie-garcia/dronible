from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QHBoxLayout
from crazydrone import find_available_drones, CrazyDrone
from riot import Riot
from PyQt5.QtCore import QTimer
import sys

"""
This examples demonstrates how to make the drone fly and display senor values
"""

# states
GROUNDED = 0
FLYING = 1
HOVERING = 2
CLIMBING = 3
DESCENDING = 4
PERFECT_FORM = 5
WORST_FORM = 6

BAD = 0
GOOD = 1

class DumbellTraining:
    def __init__(self):
        self.motion = BAD
        self.drone = None
        self.available = None
        self.riot = None
        self.riot_id = None
        self.init_drone()
        if self.drone is None:
            quit()
        self.init_sensor()
        self.init_gui()
        self.state = GROUNDED
        self.app.aboutToQuit.connect(self.riot.stop)
        self.app.aboutToQuit.connect(self.drone.stop)

        self.app.exec_()

    def init_drone(self):
        self.available = find_available_drones()
        print('availables crazyflies', str(self.available))
        if len(self.available) > 0:
            self.drone = CrazyDrone(self.available[0][0])
            self.drone.init()

    def init_sensor(self):
        self.riot_id = 2
        self.riot = Riot(self.riot_id)
        self.riot.start()
        self.riot.acc_intensity.connect(self.evaluate_motion)

    def init_gui(self):
        self.app = QApplication([])

        #buttons
        self.start_button = QPushButton("take off")
        self.stp_button = QPushButton("Land")
        # self.forward_button = QPushButton("Forward 1m")
        # self.backward_button = QPushButton("Backward 1m")
        # self.strafe_right_button = QPushButton("Strafe right 1m")
        # self.strafe_left_button = QPushButton("Strafe left 1m")
        # self.go_up_button = QPushButton("Go up")
        # self.go_down_button = QPushButton("Go  down ")
        self.start_exercise_button = QPushButton("Start exercising")
        self.stop_exercise_button = QPushButton("Stop exercising")
        self.evaluate_motion_good_button = QPushButton("WoZ good motion")
        self.evaluate_motion_bad_button = QPushButton("WoZ bad motion")

        #timers
        self.timer_altitude_check = QTimer()
        self.timer_altitude_check.timeout.connect(self.check_altitude)


        self.widget = QWidget()
        layout = QHBoxLayout()
        self.widget.setLayout(layout)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stp_button)
        layout.addWidget(self.start_exercise_button)
        layout.addWidget(self.stop_exercise_button)
        # layout.addWidget(self.forward_button)
        # layout.addWidget(self.backward_button)
        # layout.addWidget(self.strafe_left_button)
        # layout.addWidget(self.strafe_right_button)
        # layout.addWidget(self.go_down_button)
        #layout.addWidget(self.go_up_button)
        layout.addWidget(self.evaluate_motion_bad_button)
        layout.addWidget(self.evaluate_motion_good_button)

        # connect button to the drone functions
        self.start_button.clicked.connect(self.take_off)
        self.stp_button.clicked.connect(self.land)
        self.start_exercise_button.clicked.connect(self.start_exercise)
        self.stop_exercise_button.clicked.connect(self.land)
        # self.backward_button.clicked.connect(lambda: self.drone.process_motion(0, 0, -0.1, 0))
        # self.forward_button.clicked.connect(lambda: self.drone.process_motion(0, 0, 0.1, 0))
        # self.strafe_left_button.clicked.connect(lambda: self.drone.process_motion(0, 0, 0, 0.1))
        # self.strafe_right_button.clicked.connect(lambda: self.drone.process_motion(0, 0, 0, -0.1))
        # self.go_down_button.clicked.connect(lambda: self.drone.process_motion(- 0.1, 0, 0, 0))
        # self.go_up_button.clicked.connect((lambda: self.drone.process_motion(0.1, 0, 0, 0)))
        self.evaluate_motion_bad_button.clicked.connect(self.set_motion_to_bad)
        self.evaluate_motion_good_button.clicked.connect(self.set_motion_to_good)
        self.widget.show()
        self.drone.batteryValue.connect(lambda status: print('batt', status))

    def take_off(self):
        if self.state == GROUNDED:
            self.state = FLYING
            self.drone.take_off()

    def land(self):
        # usable whatever the state
        self.state = GROUNDED
        self.drone.land()

    def start_exercise(self):
        if self.state == FLYING:
            print("start exercise")
            self.state = HOVERING
            self.timer_altitude_check.start(2000)
        elif self.state == HOVERING or self.state == CLIMBING or self.state == DESCENDING or self.state == PERFECT_FORM or self.state == WORST_FORM:
            print("already exercising !")
        elif self.state == GROUNDED:
            print("Drone must takeoff before starting the exercise")

    def check_altitude(self):
        altitude = self.drone.motion_commander._thread.get_height()
        if self.state == CLIMBING:
            if altitude >= 1.8:
                self.drone.process_motion(0, 0, 0, 0)
                self.state == PERFECT_FORM
        if self.state == DESCENDING:
            if altitude <= 0.3:
                self.drone.process_motion(0, 0, 0, 0)
                self.state == WORST_FORM
        self.timer_altitude_check.start(2000)

    def request_climb(self):
        if self.state == HOVERING or self.state == DESCENDING and self.state != PERFECT_FORM:
            self.drone.process_motion(0.1, 0, 0, 0)
            self.state = CLIMBING

    def request_descent(self):
        if self.state == HOVERING or self.state == CLIMBING and self.state != WORST_FORM:
            self.drone.process_motion(-0.1, 0, 0, 0)
            self.state = DESCENDING

    def evaluate_motion(self, norm, acc_x, acc_y, acc_z):
        #if very complex computation:
        #   self.set_motion_to_good()
        #else:
        #   self.set_motion_to_bad()

        pass

    def set_motion_to_good(self):
        self.motion = GOOD

    def set_motion_to_bad(self):
        self.motion = BAD

    def check_motion(self):
        if self.motion == GOOD and (self.state == HOVERING or self.state == DESCENDING):
            self.request_climb()
        elif self.motion == BAD and (self.state == HOVERING or self.state == CLIMBING):
            self.request_descent()

if __name__=="__main__":
    training = DumbellTraining()