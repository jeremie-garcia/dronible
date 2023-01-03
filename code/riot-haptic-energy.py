from haptic import Haptic
from riot import Riot

if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    riot_id = 2
    print('creating riot')
    riot = Riot(riot_id)
    haptic = Haptic()

    state = 0
    def process_energy( _intensity, _x,_y,_z):
        print("energy", _intensity)
        haptic.set_continuous_level(_intensity / 2)

    riot.acc_intensity.connect(process_energy)
    riot.start()

    haptic.start_continuous()
    haptic.set_continuous_level(0)

    app.aboutToQuit.connect(riot.stop)
    app.aboutToQuit.connect(haptic.stop_continuous)
    sys.exit(app.exec_())