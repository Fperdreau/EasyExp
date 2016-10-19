import time
import logging


class Pause(object):
    """
    Pause class
    Simply handles breaks
    """

    __allowed_mode = ('time', 'count')

    def __init__(self, pause_mode='time', interval=0, logger=None):
        """
        Class constructor
        :param pause_mode: pause mode ('time' or 'count')
        :param interval:
        :param logger:
        """
        if pause_mode not in self.__allowed_mode:
            raise AttributeError('Invalid pause mode')
        else:
            self.__mode = pause_mode

        self.__pauseInt = interval
        self.__counter = None
        self.__elapsed = 0.0
        self.__nb_pause = 0
        self.__logger = logger if logger is not None else logging.getLogger('EasyExp')

    @property
    def status(self):
        """
        Get elapsed time since last break
        :return:
        """
        if self.__mode == 'time':
            if self.__counter is None:
                self.__counter = time.time()
                return False
            else:
                return (time.time() - self.__counter) >=self.__pauseInt
        else:
            return self.__counter >= self.__pauseInt

    def run(self, force=False):
        """
        Is it time to do a break?
        :return:
        """
        if self.__pauseInt > 0 or force:
            if self.status >= self.__pauseInt or force:
                self.__logger.info('[{0}] Pause Requested - {1:1.2f} min have elapsed since last break [{2}]'.format(
                    __name__, (time.time() - self.__counter) / 60, self.__nb_pause))
                self.reset()
                self.__nb_pause += 1
                return True
            else:
                return False
        else:
            return False

    def reset(self):
        """
        Reset timer
        :return:
        """
        self.__counter = None