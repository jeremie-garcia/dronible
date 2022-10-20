from PyQt5.QtCore import QObject, pyqtSignal
from oscpy.server import OSCThreadServer

from crazydrone import *

#

def spin(_gx, _gy, _gz):
    return _gx*_gx + _gy*_gy + _gz*_gz


class Riot(QObject):
    acc = pyqtSignal(float, float, float)
    gyro = pyqtSignal(float, float, float)
    mag = pyqtSignal(float, float, float)
    tmp = pyqtSignal(float)
    btn = pyqtSignal(int)
    switch = pyqtSignal(int)
    euler = pyqtSignal(float, float, float, float)
    quat = pyqtSignal(float, float, float, float)
    analog = pyqtSignal(float, float)
    face = pyqtSignal(int)

    def __init__(self, id):
        super().__init__()
        self.osc = OSCThreadServer()
        self.sock = None
        self.riot_id = id
        self.prev_x = self.prev_y = self.prev_z = 0
        self.prev_gx = self.prev_gy = self.prev_gz = 0

    def OSCcallback(self, *args):
        self.acc.emit(args[0], args[1], args[2])
        self.gyro.emit(args[3], args[4], args[5])
        self.mag.emit(args[6], args[7], args[8])
        self.tmp.emit(args[9])
        self.btn.emit(args[10])
        self.switch.emit(args[11])
        self.analog.emit(args[12], args[13])
        self.quat.emit(args[14], args[15], args[16], args[17])
        self.euler.emit(args[18], args[19], args[20], args[21])

    def start(self):
        try:
            port = 8000 + self.riot_id
            self.sock = self.osc.listen(address='0.0.0.0', port=port, default=True)
            address = '/' + str(self.riot_id) + '/raw'
            self.osc.bind(address.encode(), self.OSCcallback)
            print('riot id', self.riot_id, "started on port:", port)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')

    def stop(self):
        self.osc.stop_all()

    def intensity(self, _x, _y, _z):
        x = _x * _x
        y = _y * _y
        z = _z * _z

        x = x + 0.8 * self.prev_x
        y = y + 0.8 * self.prev_y
        z = z + 0.8 * self.prev_z

        self.prev_x = x
        self.prev_y = y
        self.prev_z = z

        norm = x + y + z
        return norm, x, y, z

    def spin_filtered(self, _x, _y, _z):

        x = _x + 0.8 * self.prev_gx
        y = _y + 0.8 * self.prev_gy
        z = _z + 0.8 * self.prev_gz

        self.prev_gx = x
        self.prev_gy = y
        self.prev_gz = z

        return x, y, z


if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    riot_id = 0
    print('creating riot')
    riot = Riot(riot_id)
    riot.start()

    def process_acc(_x,_y,_z):
        norm, x, y, z = riot.intensity(_x,_y,_z)
        print('intensity', norm, _x, _y, _z)

    def process_gyro(_gx,_gy, _gz):
        x, y, z = riot.spin_filtered(_gx, _gy, _gz)
        print("filtered_spin",x,y,z)
        norm = spin(_gx, _gy, _gz)

        if abs(z) > 0.01:
            _up_speed = z / 10
            print('spin Z', _up_speed)

    def process_analog(_a1, _a2):
        print('analaog', _a1, _a2)

    #riot.acc.connect(process_acc)
    riot.gyro.connect(process_gyro)
    #riot.analog.connect(process_analog)

    app.aboutToQuit.connect(riot.stop)
    sys.exit(app.exec_())
