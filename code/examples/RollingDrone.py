import sys
from crazydrone import *
from riot import *
from PyQt5.QtCore import QCoreApplication

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
            speed = gx / 2.003
        drone.process_motion(0, 0, speed, 0)


    def start_control():
        print('connected to drones')
        drone.take_off()
        app.aboutToQuit.connect(drone.land)
        riot.gyro.connect(process_gyro)


    drone.connection.connect(start_control)

app.aboutToQuit.connect(riot.stop)
sys.exit(app.exec_())
