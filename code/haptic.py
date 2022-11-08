from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QSoundEffect


class Haptic:

    def __init__(self):
        self.fade_in_snd = QSoundEffect()
        self.fade_in_snd.setSource(QUrl.fromLocalFile('./sounds/fadeIn.wav'))
        self.fade_in_snd.setVolume(1)

        self.fade_out_snd = QSoundEffect()
        self.fade_out_snd.setSource(QUrl.fromLocalFile('./sounds/fadeOut.wav'))
        self.fade_out_snd.setVolume(1)

        self.beep_snd = QSoundEffect()
        self.beep_snd.setSource(QUrl.fromLocalFile('./sounds/beep.wav'))
        self.beep_snd.setVolume(1)

        self.cont_snd = QSoundEffect()
        self.cont_snd.setSource(QUrl.fromLocalFile('./sounds/beep.wav'))
        self.cont_snd.setVolume(1)
        self.cont_snd.setLoopCount(QSoundEffect.Infinite)

    def fade_in(self):
        self.fade_in_snd.play()

    def fade_out(self):
        self.fade_out_snd.play()

    def beep(self):
        self.beep_snd.play()

    def start_continuous(self):
        self.cont_snd.play()

    def stop_continuous(self):
        self.cont_snd.stop()

    def set_continuous_level(self, amplitude):
        self.cont_snd.setVolume(amplitude)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QPushButton, QCheckBox, QSlider

    app = QApplication([])
    haptic = Haptic()

    start_button = QPushButton("Fade In")
    stp_button = QPushButton("Fade out")
    beep_button = QPushButton("Beep")
    cont_toggle = QCheckBox("Continuous")
    cont_slider = QSlider()

    widget = QWidget()
    layout = QHBoxLayout()
    widget.setLayout(layout)
    layout.addWidget(start_button)
    layout.addWidget(stp_button)
    layout.addWidget(beep_button)
    layout.addWidget(cont_toggle)
    layout.addWidget(cont_slider)

    start_button.clicked.connect(haptic.fade_in)
    stp_button.clicked.connect(haptic.fade_out)
    beep_button.clicked.connect(haptic.beep)
    def control_continuous():
        if cont_toggle.isChecked():
            haptic.start_continuous()
        else :
            haptic.stop_continuous()

    cont_toggle.stateChanged.connect(control_continuous)

    cont_slider.valueChanged.connect(lambda val: haptic.set_continuous_level(val/100))

    widget.show()
    sys.exit(app.exec_())
    drone.stop()

    sys.exit(app.exec_())
