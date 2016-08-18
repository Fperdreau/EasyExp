from core.Core import Core
from core.display.fpscounter import FpsCounter


class BaseTrial(object):

    homeMsg = "Welcome"

    def __init__(self, core=Core):
        """
        BaseTrial constructor
        Parameters
        ----------
        core: Core instance
        :type core: Core
        """
        ##################################
        # DO NOT MODIFY THE LINES BELLOW #
        ##################################
        self.core = core
        self.screen = core.screen
        self.trial = core.trial
        self.user = core.user
        self.ptw = self.screen.ptw
        self.textToDraw = BaseTrial.homeMsg

        # State Machine
        # =============
        self.state_machine = {
            'current': None,
            'status': False,
            'timer': None,
            'duration': 0.0,
            'onset': 0.0,
            'offset': 0.0
        }
        self.status = True
        self.state = 'idle'
        self.nextState = "iti"
        self.singleShot = True  # Enable single shot events
        self.validTrial = False

        # Dependencies
        # ============
        # FPScounter: measures flip duration or simply flips the screen
        self.fpsCounter = FpsCounter(self.screen.ptw)

        # Logger: verbose level can be set by changing level to 'debug', 'info' or 'warning'
        self.logger = core.logger

        # Stimuli
        # =======
        self.stimuli = dict()

        # Devices
        # =======
        self.devices = dict()

        # Audio/Video
        # ===========
        # Initialize audio
        self.sounds = dict()
        self.movie = None

        # Timings
        # =======
        self.timings = self.trial.parameters['durations']

        # Keyboard/Mouse inputs
        self.buttons = dict()
