import sys
from drone.crazydrone import find_available_drones, CrazyDrone
from riot import Riot
from PyQt5.QtCore import QCoreApplication

'''
This example uses rotation on the X axis to make the drone move forward or backward
'''

app = QCoreApplication([])
riot_id = 0
print('creating riot')
riot = Riot(riot_id)
riot.start()
print('Finding available drones')

available = find_available_drones()
print('availables', str(available))
if len(available) > 0:
    drone = CrazyDrone(available[0][0])


    def process_gyro(gx, gy, gz):
        speed = 0
        if abs(gx) > 0.3:
            speed = gx / 2.00
        drone.process_motion(0, 0, speed, 0)


    def start_control():
        print('connected to drones')
        drone.take_off()
        app.aboutToQuit.connect(drone.land)
        riot.gyro.connect(process_gyro)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
sys.exit(app.exec_())
