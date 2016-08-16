from psychopy import event
import pygame


class Buttons(object):
    """
    Buttons class
    Handles keyboard/mouse inputs
    """

    allowed = {'mouse', 'keyboard'}

    def __init__(self, ptw, device, buttons):
        """
        :param device
        :param dict buttons:
        :return:
        """
        if device not in self.allowed:
            raise("'{}' is not supported.".format(device))

        self.device_type = device
        if device == 'keyboard':
            self.device = pygame.key
        elif device == 'mouse':
            self.device = event.Mouse(visible=False, newPos=None, win=ptw)

        self.buttons = buttons
        self.status = {}
        self.init_buttons()

    def init_buttons(self):
        """
        Reset every buttons status to their initial value
        :return:
        """
        for button, ind in self.buttons.iteritems():
            self.status[button] = False

    def get(self):
        """
        Get buttons state
        :return:
        """
        self.init_buttons()
        pygame.event.pump()
        if self.device == 'keyboard':
            keys = self.device.get_pressed()
        else:
            keys = self.device.getPressed()

        for button, ind in self.buttons.iteritems():
            self.status[button] = keys[ind] == 1
        pygame.event.clear()

    @property
    def position(self):
        """
        Get device position (only for mouse; otherwise returns None)
        Returns
        -------
        position: tuple
        """
        if self.device_type == 'mouse':
            return self.device.getPos()
        else:
            return None
