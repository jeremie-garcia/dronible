import math
import time

from PyQt5.QtCore import QObject, pyqtSignal
from oscpy.server import OSCThreadServer

"""
This module provides a class and utilities to work with riot sensors.
Many code is borrowed from https://github.com/Ircam-R-IoT/motion-analysis-firmware to perform motion analysis.
author jeremie.garcia@enac.fr
"""

ACC_INTENSITY_PARAM1 = 0.8
ACC_INTENSITY_PARAM2 = 0.1

GYR_INTENSITY_PARAM1 = 0.8
GYR_INTENSITY_PARAM2 = 0.1

FREEFALL_ACC_THRESHOLD = 0.15
FREEFALL_GYR_THRESHOLD = 7.50
FREEFALL_GYR_DELTA_THRESHOLD = 40

KICK_THRESHOLD = 0.01
KICK_SPEEDGATE = 200
KICK_MEDIAN_FILTERSIZE = 9

SHAKE_THRESHOLD = 0.1
SHAKE_WINDOWSIZE = 10
SHAKE_SLIDE_FACTOR = 10

SPIN_THRESHOLD = 0.2

STILL_THRESHOLD = 0.0005
STILL_SLIDE_FACTOR = 5.0

DELTA_TIME = 5

def delta(previous, next, dt):
    return (next - previous) / (2 * dt)


def intensity1D(xnext, xprev, intensityprev, param1, param2, dt):
    dx = delta(xprev, xnext, dt)
    return param2 * dx * dx + param1 * intensityprev


# least commom multiplier
def lcm(a, b):
    a1 = a
    b1 = b
    while a1 != b1:
        if a1 < b1:
            a1 += a
        else:
            b1 += b

    return a1


def magnitude3D(x, y, z):
    return math.sqrt(x * x + y * y + z * z)


def slide(previous_y, current_x, slide_factor):
    return previous_y + (current_x - previous_y) / slide_factor


def still_cross_product(x, y, z):
    return (y - z) * (y - z) + (x - y) * (x - y) + (z - x) * (z - x)


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

    # processed signals
    acc_intensity = pyqtSignal(float, float, float, float)
    gyr_intensity = pyqtSignal(float, float, float, float)
    freefall = pyqtSignal(float, float, float)
    kick = pyqtSignal(float, float)
    shake = pyqtSignal(float)
    spin = pyqtSignal(float, float, float)
    still = pyqtSignal(float, float)

    def __init__(self, id):
        super().__init__()
        self.osc = OSCThreadServer()
        self.sock = None
        self.riot_id = id

        self.LoopIndex = 0
        # for acceleration intensity
        self.acc_last_three = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
        self.acc_intensity_last_two = [[0., 0.], [0., 0.], [0., 0.]]

        # for gyration intensity
        self.gyr_last_three = [[0., 0., 0.], [0., 0., 0.], [0., 0., 0.]]
        self.gyr_intensity_last_two = [[0., 0.], [0., 0.], [0., 0.]]

        # for freefall
        self.acc_norm = 0
        self.gyr_delta = [0, 0, 0]
        self.gyr_norm = self.gyr_delta_norm = 0
        self.FallBegin = 0
        self.FallEnd = 0
        self.fallDuration = self.isFalling = 0.0

        # for kick
        self.kick_intensity = 0.0
        self.LastKick = 0
        self.isKicking = 0
        self.median_values = [0., 0., 0., 0., 0., 0., 0., 0., 0.]
        self.median_linking = [3, 4, 1, 5, 7, 8, 0, 2, 6]
        self.median_fifo = [6, 2, 7, 0, 1, 3, 8, 4, 5]
        self.i1 = self.i2 = self.i3 = 0
        self.acc_intensity_norm_median = 0

        # for shake
        self.acc_delta = [0, 0, 0]
        self.shake_window = [[0 for y in range(SHAKE_WINDOWSIZE)] for x in range(3)]
        self.shake_nb = [0, 0, 0]
        self.shaking_raw = 0
        self.shake_slide_prev = 0

        # for spin
        self.SpinBegin = 0
        self.SpinEnd = 0
        self.spinDuration = 0
        self.isSpinning = 0

        # for still
        self.still_slide_prev = 0

        self.LoopIndexPeriod = lcm(lcm(lcm(2, 3), KICK_MEDIAN_FILTERSIZE), SHAKE_WINDOWSIZE)

    def OSCcallback(self, *args):
        self.acc.emit(args[0], args[1], args[2])
        self.gyro.emit(args[3], args[4], args[5])
        self.mag.emit(args[6], args[7], args[8])
        self.tmp.emit(args[9])
        self.btn.emit(args[10])
        self.analog.emit(args[12], args[13])
        self.quat.emit(args[14], args[15], args[16], args[17])
        self.euler.emit(args[18], args[19], args[20], args[21])

        elapsedTime = round(time.time() * 1000)
        # Acceleration Intensity
        a_x = args[0]
        a_y = args[1]
        a_z = args[2]
        self.acc_last_three[0][self.LoopIndex % 3] = a_x
        self.acc_last_three[1][self.LoopIndex % 3] = a_y
        self.acc_last_three[2][self.LoopIndex % 3] = a_z

        acc_intensity_x = intensity1D(a_x, self.acc_last_three[0][(self.LoopIndex + 1) % 3],
                                      self.acc_intensity_last_two[0][(self.LoopIndex + 1) % 2], ACC_INTENSITY_PARAM1,
                                      ACC_INTENSITY_PARAM2, 1)
        self.acc_intensity_last_two[0][self.LoopIndex % 2] = acc_intensity_x

        acc_intensity_y = intensity1D(a_y, self.acc_last_three[1][(self.LoopIndex + 1) % 3],
                                      self.acc_intensity_last_two[1][(self.LoopIndex + 1) % 2], ACC_INTENSITY_PARAM1,
                                      ACC_INTENSITY_PARAM2, 1)
        self.acc_intensity_last_two[1][self.LoopIndex % 2] = acc_intensity_y

        acc_intensity_z = intensity1D(a_z, self.acc_last_three[2][(self.LoopIndex + 1) % 3],
                                      self.acc_intensity_last_two[2][(self.LoopIndex + 1) % 2], ACC_INTENSITY_PARAM1,
                                      ACC_INTENSITY_PARAM2, 1)
        self.acc_intensity_last_two[2][self.LoopIndex % 2] = acc_intensity_z;

        acc_intensity_norm = acc_intensity_x + acc_intensity_y + acc_intensity_z
        self.acc_intensity.emit(acc_intensity_norm, acc_intensity_x, acc_intensity_y, acc_intensity_z)

        # GYRO INTENSITY
        g_x = args[3]
        g_y = args[4]
        g_z = args[5]
        self.gyr_last_three[0][self.LoopIndex % 3] = g_x
        self.gyr_last_three[1][self.LoopIndex % 3] = g_y
        self.gyr_last_three[2][self.LoopIndex % 3] = g_z

        gyr_intensity_x = intensity1D(a_x, self.gyr_last_three[0][(self.LoopIndex + 1) % 3],
                                      self.gyr_intensity_last_two[0][(self.LoopIndex + 1) % 2], GYR_INTENSITY_PARAM1,
                                      GYR_INTENSITY_PARAM2, DELTA_TIME)
        self.gyr_intensity_last_two[0][self.LoopIndex % 2] = gyr_intensity_x

        gyr_intensity_y = intensity1D(a_y, self.gyr_last_three[1][(self.LoopIndex + 1) % 3],
                                      self.gyr_intensity_last_two[1][(self.LoopIndex + 1) % 2], GYR_INTENSITY_PARAM1,
                                      GYR_INTENSITY_PARAM2, DELTA_TIME)
        self.gyr_intensity_last_two[1][self.LoopIndex % 2] = gyr_intensity_y

        gyr_intensity_z = intensity1D(a_z, self.gyr_last_three[2][(self.LoopIndex + 1) % 3],
                                      self.gyr_intensity_last_two[2][(self.LoopIndex + 1) % 2], GYR_INTENSITY_PARAM1,
                                      GYR_INTENSITY_PARAM2, DELTA_TIME)
        self.gyr_intensity_last_two[2][self.LoopIndex % 2] = gyr_intensity_z;

        gyr_intensity_norm = gyr_intensity_x + gyr_intensity_y + gyr_intensity_z
        self.gyr_intensity.emit(gyr_intensity_norm, gyr_intensity_x, gyr_intensity_y, gyr_intensity_z)

        # FREEFALL
        acc_norm = magnitude3D(a_x, a_y, a_z)
        gyr_norm = magnitude3D(g_x, g_y, g_z)
        self.gyr_delta[0] = delta(self.gyr_last_three[0][(self.LoopIndex + 1) % 3], g_x, DELTA_TIME)
        self.gyr_delta[1] = delta(self.gyr_last_three[1][(self.LoopIndex + 1) % 3], g_y, DELTA_TIME)
        self.gyr_delta[2] = delta(self.gyr_last_three[2][(self.LoopIndex + 1) % 3], g_z, DELTA_TIME)
        gyr_delta_norm = magnitude3D(self.gyr_delta[0], self.gyr_delta[1], self.gyr_delta[2])

        if (acc_norm < FREEFALL_ACC_THRESHOLD or (
                gyr_norm > FREEFALL_GYR_THRESHOLD and gyr_delta_norm < FREEFALL_GYR_DELTA_THRESHOLD)):
            # Falling state detected
            if self.isFalling == 0.0:
                self.isFalling = 1.0
                self.FallBegin = round(time.time() * 1000)

            self.FallEnd = round(time.time() * 1000)

        else:
            if self.isFalling == 1.0:
                self.isFalling = 0.0

        self.fallDuration = float(self.FallEnd - self.FallBegin)
        self.freefall.emit(acc_norm, self.isFalling, self.fallDuration)


        # KICK
        i3 = self.LoopIndex % KICK_MEDIAN_FILTERSIZE
        i1 = self.median_fifo[i3]
        i2 = 1

        if i1 < KICK_MEDIAN_FILTERSIZE - 1 and acc_intensity_norm > self.median_values[i1 + i2]:
            while i1 + i2 < KICK_MEDIAN_FILTERSIZE and acc_intensity_norm > self.median_values[i1 + i2]:
                self.median_fifo[self.median_linking[i1 + i2]] = self.median_fifo[self.median_linking[i1 + i2]] - 1
                self.median_values[i1 + i2 - 1] = self.median_values[i1 + i2]
                self.median_linking[i1 + i2 - 1] = self.median_linking[i1 + i2]
                i2 = i2 + 1

            self.median_values[i1 + i2 - 1] = acc_intensity_norm
            self.median_linking[i1 + i2 - 1] = i3
            self.median_fifo[i3] = i1 + i2 - 1

        else:
            while i2 < i1 + 1 and acc_intensity_norm < self.median_values[i1 - i2]:
                self.median_fifo[self.median_linking[i1 - i2]] = self.median_fifo[self.median_linking[i1 - i2]] + 1
                self.median_values[i1 - i2 + 1] = self.median_values[i1 - i2]
                self.median_linking[i1 - i2 + 1] = self.median_linking[i1 - i2]
                i2 = i2 + 1

            self.median_values[i1 - i2 + 1] = acc_intensity_norm
            self.median_linking[i1 - i2 + 1] = i3
            self.median_fifo[i3] = i1 - i2 + 1

        if acc_intensity_norm - self.acc_intensity_norm_median > KICK_THRESHOLD:
            if self.isKicking == 1:
                if self.kick_intensity < acc_intensity_norm:
                    self.kick_intensity = acc_intensity_norm
            else:
                self.isKicking = 1
                self.kick_intensity = acc_intensity_norm
                self.LastKick = elapsedTime
        else:
            if elapsedTime - self.LastKick > KICK_SPEEDGATE:
                self.isKicking = 0

        acc_intensity_norm_median = self.median_values[round(KICK_MEDIAN_FILTERSIZE / 2)]
        self.kick.emit(self.kick_intensity, self.isKicking)

        # SHAKING
        self.acc_delta[0] = delta(self.acc_last_three[0][(self.LoopIndex + 1) % 3], a_x, DELTA_TIME)
        self.acc_delta[1] = delta(self.acc_last_three[1][(self.LoopIndex + 1) % 3], a_y, DELTA_TIME)
        self.acc_delta[2] = delta(self.acc_last_three[2][(self.LoopIndex + 1) % 3], a_z, DELTA_TIME)

        for k in range(3):
            if self.shake_window[k][self.LoopIndex % SHAKE_WINDOWSIZE]:
                self.shake_nb[k] = self.shake_nb[k] - 1

            if self.acc_delta[k] > SHAKE_THRESHOLD:
                self.shake_window[k][self.LoopIndex % SHAKE_WINDOWSIZE] = 1
                self.shake_nb[k] = self.shake_nb[k] + 1

            else:
                self.shake_window[k][self.LoopIndex % SHAKE_WINDOWSIZE] = 0

        shaking_raw = magnitude3D(self.shake_nb[0], self.shake_nb[1], self.shake_nb[2]) / SHAKE_WINDOWSIZE
        shaking = slide(self.shake_slide_prev, shaking_raw, SHAKE_SLIDE_FACTOR)
        self.shake_slide_prev = shaking
        self.shake.emit(shaking)

        # SPIN
        if gyr_norm > SPIN_THRESHOLD:
            if self.isSpinning == 0.:
                self.isSpinning = 1.
                self.SpinBegin = round(time.time() * 1000)

            self.SpinEnd = round(time.time() * 1000)

        elif self.isSpinning == 1:
            self.isSpinning = 0

        spinDuration = float(self.SpinEnd - self.SpinBegin)
        self.spin.emit(self.isSpinning, spinDuration, gyr_norm)

        # still
        still_crossprod = still_cross_product(g_x, g_y, g_z)
        still_slide = slide(self.still_slide_prev, still_crossprod, STILL_SLIDE_FACTOR)
        if still_slide > STILL_THRESHOLD:
            isStill = 0
        else:
            isStill = 1
        self.still_slide_prev = still_slide
        self.still.emit(isStill, still_slide)

        self.LoopIndex = (self.LoopIndex + 1) % self.LoopIndexPeriod

    def start(self):
        try:
            port = 8888
            self.sock = self.osc.listen(address='0.0.0.0', port=port, default=True)
            address = '/' + str(self.riot_id) + '/raw'
            self.osc.bind(address.encode(), self.OSCcallback)
            print('riot id', self.riot_id, "started on port:", port)
        except KeyboardInterrupt:
            self.osc.stop_all()
            print('stopped all for keyboard interupt')

    def stop(self):
        self.osc.stop_all()

    def temp_to_celsius(self, temp_f):
        return temp_f / 8. + 21  # from example code so not sure about original units.


if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    riot_id = 1
    print('creating riot')
    riot = Riot(riot_id)


    def print_tmp(temp_k):
        temp_c = riot.temp_to_celsius(temp_k)
        print('Temperatire K', temp_k, 'celsius:', temp_c)

    def print_euler(_a1, _a2, _a3, _a4):
        print('Yaw', "{:.1f}".format(_a1), "pitch", "{:.1f}".format(_a2), "roll", "{:.1f}".format(_a3), 'heading',
              "{:.1f}".format(_a4))

    def print_falling(_acc, _falling, _duration):
        print('Falling', "{:.0f}".format(_falling), "Duration", "{:.1f}".format(_duration), "_acc", "{:.1f}".format(_acc))


    def print_kick( _intensity, _kicking):
        print('Kicking', "{:.0f}".format(_kicking), "Intensity", "{:.2f}".format(_intensity))

    def print_spinning( _spinning, _duration, _gyr_norm):
        print('Spining', "{:.0f}".format(_spinning), "duration", _duration , "Intensity", "{:.2f}".format(_gyr_norm))


    # uncomment to see the data
    # riot.acc.connect(
    #    lambda _x, _y, _z: print('Acceleration RAW', "{:.2f}".format(_x), "{:.2f}".format(_y), "{:.2f}".format(_z)))
    # riot.gyro.connect(
    #    lambda _x, _y, _z: print('Gyroscope RAW', "{:.2f}".format(_x), "{:.2f}".format(_y), "{:.2f}".format(_z)))
    # riot.mag.connect(
    #    lambda _x, _y, _z: print('Magnetometer RAW', "{:.2f}".format(_x), "{:.2f}".format(_y), "{:.2f}".format(_z)))

    # riot.tmp.connect(print_tmp)
    # riot.btn.connect(lambda btn: print('btn state:', btn))
    # riot.analog.connect(lambda  _a1, _a2 : print('analaog raw', _a1, _a2))
    # riot.quat.connect(lambda a, b, c, d: print('Quat', a, b, c, d)
    # riot.euler.connect(print_euler)
    # riot.acc_intensity.connect(lambda _intensity, _x, _y, _z: print('Acceleration Intensity', "{:.2f}".format(_intensity), "{:.2f}".format(_x), "{:.2f}".format(_y), "{:.2f}".format(_z)))
    # riot.gyr_intensity.connect(lambda _intensity, _x, _y, _z: print('Gyration Intensity', "{:.2f}".format(_intensity), "{:.2f}".format(_x), "{:.2f}".format(_y), "{:.2f}".format(_z)))
    riot.freefall.connect(print_falling)
    # riot.kick.connect(print_kick)
    # riot.shake.connect(print)
    # riot.spin.connect(print_spinning)
    riot.still.connect(lambda _still, _slide: print("Still?", _still, "slide", _slide))

    riot.start()

    app.aboutToQuit.connect(riot.stop)
    sys.exit(app.exec_())
