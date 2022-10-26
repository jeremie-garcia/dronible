from PyQt5.QtCore import QObject, pyqtSignal
from oscpy.server import OSCThreadServer


class Riot(QObject):
    '''
    Creates a Bitalino Riot object for retrieving data and using higher level descriptors

    The class provides several qt5 signals

    acc: 3 axis accelerometer (1 float per axis) {-8 ; +8} g
    gyro: 3 axis gyroscope {-2 ; +2} °/s
    mag: 3 axis magnetometer {-2 ; +2} gauss
    tmp_K: Temperature °K
    btn: Mode Switch {0 / 1} (float)
    analog: Analog Inputs (GPIO3 & GPIO4) {0 ; 4095}
    quat : Quaternions {-1 ; 1}
    euler: Euler Angles and Heading {-180 ; 180} °

    '''
    acc = pyqtSignal(float, float, float)
    gyro = pyqtSignal(float, float, float)
    mag = pyqtSignal(float, float, float)
    tmp = pyqtSignal(float)
    btn = pyqtSignal(float)
    analog = pyqtSignal(float, float)
    quat = pyqtSignal(float, float, float, float)
    euler = pyqtSignal(float, float, float, float)

    def __init__(self, id):
        super().__init__()
        self.osc = OSCThreadServer()
        self.sock = None
        self.riot_id = id
        self.prev_acc = self.prev_spin = [0,0,0]

    def OSCcallback(self, *args):
        self.acc.emit(args[0], args[1], args[2])
        self.gyro.emit(args[3], args[4], args[5])
        self.mag.emit(args[6], args[7], args[8])
        self.tmp.emit(args[9])
        self.btn.emit(args[10])
        self.analog.emit(args[12], args[13])
        self.quat.emit(args[14], args[15], args[16], args[17])
        self.euler.emit(args[18], args[19], args[20], args[21])

    def start(self):
        try:
            port = 8888 + self.riot_id
            self.sock = self.osc.listen(address='0.0.0.0', port=port, default=True)
            address = '/' + str(self.riot_id) + '/raw'
            self.osc.bind(address.encode(), self.OSCcallback)
            print('riot id', self.riot_id, "started on port:", port)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')

    def stop(self):
        self.osc.stop_all()

    def acc_intensity(self, _x, _y, _z):
        # compute derivative from  last samples
        avrg_x = (_x - self.prev_acc[0]) / 2
        avrg_y = (_y - self.prev_acc[1]) / 2
        avrg_z = (_z - self.prev_acc[2]) / 2

        # stor the previous values
        self.prev_acc[0] = _x
        self.prev_acc[1] = _y
        self.prev_acc[2] = _z

        x_norm = (avrg_x * avrg_x)
        y_norm = (avrg_y * avrg_y)
        z_norm = (avrg_z * avrg_z)

        norm = x_norm + y_norm + z_norm
        return norm, x_norm, y_norm, z_norm

    def spin_intensity(self, _x, _y, _z):
        # compute derivative from  last samples
        avrg_x = (_x - self.prev_spin[0]) / 2
        avrg_y = (_y - self.prev_spin[1]) / 2
        avrg_z = (_z - self.prev_spin[2]) / 2

        # stor the previous values
        self.prev_spin[0] = _x
        self.prev_spin[1] = _y
        self.prev_spin[2] = _z

        x_norm = (avrg_x * avrg_x)
        y_norm = (avrg_y * avrg_y)
        z_norm = (avrg_z * avrg_z)

        norm = x_norm + y_norm + z_norm
        return norm, x_norm, y_norm, z_norm


    def temp_to_celsius(self, temp_f):
        return temp_f / 8. + 21  # from example code so not sure about original units.


if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    riot_id = 0
    print('creating riot')
    riot = Riot(riot_id)
    riot.start()


    def process_acc(_x, _y, _z):
        norm, x, y, z = riot.acc_intensity(_x, _y, _z)
        print('Acceleration intensity', "{:.2f}".format(norm), "acc raw", _x, _y, _z)


    def process_gyro(_gx, _gy, _gz):
        norm, x, y, z = riot.spin_intensity(_gx, _gy, _gz)
        print('Gyro intensity:', norm, "Gyro Raw:", _gx, _gy, _gz)


    def process_mag(_mx, _my, _mz):
        print('Magnetormer Raw', _mx, _my, _mz)


    def process_tmp(temp_k):
        temp_c = riot.temp_to_celsius(temp_k)
        print('Temperatire K', temp_k, 'celsius:', temp_c)


    def process_btn(btn):
        print('btn state:', btn)


    def process_analog(_a1, _a2):
        print('analaog raw', _a1, _a2)


    def process_quat(_a1, _a2, _a3, _a4):
        print('Quat raw', _a1, _a2, _a3, _a4)


    def process_euler(_a1, _a2, _a3, _a4):
        print('Yaw', "{:.1f}".format(_a1), "pitch", "{:.1f}".format(_a2), "roll", "{:.1f}".format(_a3), 'heading', "{:.1f}".format(_a4))


    #uncomment to see the data
    #riot.acc.connect(process_acc)
    #riot.gyro.connect(process_gyro)
    #riot.mag.connect(process_mag)
    #riot.tmp.connect(process_tmp)
    #riot.btn.connect(process_btn)
    #riot.analog.connect(process_analog)
    #riot.quat.connect(process_quat)
    #riot.euler.connect(process_euler)

    app.aboutToQuit.connect(riot.stop)
    sys.exit(app.exec_())
