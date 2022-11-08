from haptic import Haptic
from riot import Riot

if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QCoreApplication

    app = QCoreApplication([])
    riot_id = 1
    print('creating riot')
    riot = Riot(riot_id)
    haptic = Haptic()

    state = 0
    def process_kick( _intensity, _kicking):
        print('Kicking', "{:.0f}".format(_kicking), "Intensity", "{:.2f}".format(_intensity))
        if _kicking :
            haptic.beep()


    def process_kick2(_intensity, _kicking):
        print('Kicking', "{:.0f}".format(_kicking), "Intensity", "{:.2f}".format(_intensity))
        if _kicking:
            haptic.start_continuous()
            haptic.set_continuous_level(_intensity/10)
        else:
            haptic.stop_continuous()

    riot.kick.connect(process_kick2)
    riot.start()

    app.aboutToQuit.connect(riot.stop)
    sys.exit(app.exec_())
