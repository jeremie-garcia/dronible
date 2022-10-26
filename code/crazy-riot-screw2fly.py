import sys
from drone.crazydrone import find_available_drones, CrazyDrone
from riot import Riot

from PyQt5.QtCore import QCoreApplication

#this example uses rotation on the Z axis to make the drone takeoff above a certin threshold.
# then the roation is used to compute the vertical speed (in both directions)



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
    try:
        drone = CrazyDrone(available[0][0])

        def process_gyro(_x, _y, _z):
            global state

            if drone.motion_commander is not None:
                x, y, z = riot.spin_filtered(_x, _y, _z)
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

    except KeyboardInterrupt:
        riot.stop()
        drone.land()


app.aboutToQuit.connect(riot.stop)
app.aboutToQuit.connect(drone.land)
sys.exit(app.exec_())
