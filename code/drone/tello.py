import re
import socket
import sys
from threading import Thread

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QPushButton

from drone.drone import Drone

INTERVAL = 1


def clamp(x):
    return round(min(100, max(-100, x)))


class TelloDrone(Drone):
    tempValue = pyqtSignal(int)  # value: 'between 0 and 100'

    def __init__(self):
        super().__init__()

        self.local_ip = ''

        # socket for receiving cmd ack
        self.cmd_port = 8889
        self.cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cmd_sock.bind((self.local_ip, self.cmd_port))

        # socket for receiving state values
        self.state_port = 8890
        self.state_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_sock.bind((self.local_ip, self.state_port))

        self.tello_address = ('192.168.10.1', self.cmd_port)

        self.running = True
        # thread for receiving cmd ack
        self.receive_cmd_thread = Thread(target=self._receive_cmd_thread)
        self.receive_cmd_thread.daemon = True
        self.receive_cmd_thread.start()

        # thread for receiving state
        self.receive_state_thread = Thread(target=self._receive_state_thread)
        self.receive_state_thread.daemon = True
        self.receive_state_thread.start()

        self.state_response = ""
        self.cmd_response = ""
        self.cmd_state = ""
        self._is_flying = False
        self.prev_cmd = ""


    def send_command(self, cmd):
        #print(cmd,"cmd sent to tello")
        self.cmd_sock.sendto(cmd.encode(encoding="utf-8"), self.tello_address)

    def init(self):
        self.cmd_state = "cmd"
        self.connection.emit("off")
        self.send_command('command')

    def take_off(self):
        if not self.is_flying():
            self.cmd_state = "takeoff"
            self.send_command('takeoff')

    def land(self):
        self.cmd_state = "land"
        self.send_command('land')

    def stop(self):
        self.land()
        self.running = False
        self.state_sock.close()
        self.cmd_sock.close()

    def _receive_cmd_thread(self):
        """Listen to responses from the Tello.
        Runs as a thread, sets self.response to whatever the Tello last returned.
        """
        while self.running:
            try:
                rep, ip = self.cmd_sock.recvfrom(1024)
                self.cmd_response = rep.decode('utf8')
                if self.cmd_response == 'ok':
                    if self.cmd_state == 'cmd':
                        print('tello connected')
                        self.connection.emit('on')
                    if self.cmd_state == 'takeoff':
                        self._is_flying = True
                        self.is_flying_signal.emit(True)
                    if self.cmd_state == 'land':
                        self._is_flying = False
                        self.is_flying_signal.emit(False)

                    print("command", self.cmd_state, "ACK")
                else:
                    print("command,", self.cmd_state, 'error', self.cmd_response)

                self.cmd_state = ""
            except socket.error as exc:
                print("CMD ERROR: %s" % exc)

    def _receive_state_thread(self):
        """Listen to responses from the Tello.
        Runs as a thread, sets self.response to whatever the Tello last returned.
        """
        while self.running:
            try:
                rep, ip = self.state_sock.recvfrom(1024)
                self.state_response = rep.decode('utf8')

                #temp = re.search(r"temph:(\d*)", self.state_response).group()[6:]
                #self.tempValue.emit(int(temp))  # hack...
                #print("temperature", temp)
                bat = re.search(r"bat:(\d*)", self.state_response).group()[4:]
                self.batteryValue.emit(int(bat) * 0.043)  # hack...
            except socket.error as exc:
                print("CMD ERROR: %s" % exc)

    def is_flying(self):
        return self._is_flying

    def process_motion(self, _up, _rotate, _front, _right):
        '''
        Need to be in -100 100 range for each commands
        '''

        if self.is_flying():
            velocity_up_down = clamp(_up * 50 * self.max_vert_speed)
            velocity_yaw = clamp(_rotate/180 * 100 * self.max_rotation_speed)
            velocity_front_back = clamp(_front * 50 * self.max_horiz_speed)
            velocity_left_right = clamp(_right * 50 * self.max_horiz_speed)
            cmd = f"rc {velocity_left_right} {velocity_front_back} {velocity_up_down} {velocity_yaw}"
            #print("TELLO:", cmd)
            self.cmd_state = "rc"
            self.send_command(cmd)


if __name__ == "__main__":
    app = QApplication([])
    tello = TelloDrone()
    button = QPushButton("start")
    stp_button = QPushButton("stop")
    button.clicked.connect(tello.take_off)
    stp_button.clicked.connect(tello.land)
    button.show()
    stp_button.show()
    tello.batteryValue.connect(lambda status: print('batt', status))
    tello.is_flying_signal.connect(lambda status: print('flying?', status))
    tello.connection.connect(lambda status: print('connection', status))
    tello.init()
    sys.exit(app.exec_())
    tello.stop()
