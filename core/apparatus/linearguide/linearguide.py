from core.apparatus.optotrak.optotrak import OptoTrak


class LinearGuide(object):

    __tracker = None  # Tracker instance
    sensors_label = ('Xas', 'Marker2', 'Yas', 'origin', 'hand1', 'hand2')  # Sensors label
    center_from_edge = -0.50  # Distance of guide center from right edge (in m)

    def __init__(self, dummy_mode=False, user_file='', sensitivity=1.0, velocity_threshold=0.01, time_threshold=0.100):
        """
        LinearGuide constructor
        :param dummy_mode:
        :param user_file:
        :param sensitivity:
        :param velocity_threshold:
        :param time_threshold:
        """
        self.__sensitivity = sensitivity
        self.__velocity_threshold = velocity_threshold
        self.__time_threshold = time_threshold
        self.__user_file = user_file
        self.__dummy_mode = dummy_mode

        # Get optotrak
        self.get_tracker()

    def get_tracker(self):
        """
        Factory: Get Optotrak instance
        :rtype: OptoTrak
        """
        if self.__tracker is None:
            self.__tracker = OptoTrak(user_file=self.__user_file, freq=200.0,
                                      velocity_threshold=self.__velocity_threshold,
                                      time_threshold=self.__time_threshold, origin='origin',
                                      labels=LinearGuide.sensors_label,
                                      dummy_mode=self.__dummy_mode,
                                      tracked=dict(self.sensors_label))
            self.__tracker.init()
        return self.__tracker

    def start_trial(self, trial_id, params):
        """
        Start trial routine
        :param trial_id:
        :param params:
        :return:
        """
        self.__tracker.start_trial(trial=trial_id, param=params)

    def stop_trial(self, trial_id, valid=True):
        self.__tracker.stop_trial(trial=trial_id, valid=valid)

    @property
    def position(self):
        """
        Return position of slider in guide coordinates (centered on guide center).
        :rtype: ndarray
        """
        return self.__tracker.sensors['hand2'].position - self.__tracker.sensors['hand1'].position


if __name__ == '__main__':
    guide = LinearGuide()
