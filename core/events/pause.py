class Pause():
    """
    Do a break
    """

    msg = "Time to take a break.\n Press any button to start again"

    def __init__(self, win, pause_time):
        self.pauseTime = pause_time
        self.win = win
        self.text = visual.TextStim(self.win, text=self.msg, pos=(.5, 0))
        self.status = 0
        self.init_time = time.time()

        self.dopause()

    def dopause(self):
        if time.time() - self.init_time >= self.pauseTime:
            print 'Take a break, have a KitKat'
            print 'You had %d break(s) sor far' % self.status
            self.init_time = time.time()

            self.pause_experiment()
            self.show_msg()
            self.restart_experiment()
            self.status += 1

    def show_msg(self):
        # Show message until the user presses a key
        ind_resp = None
        while ind_resp is None:
            ind_resp = getResponse()
            self.text.draw()
            win.flip()

    def pause_experiment(self):
        # Add some time to avoid any interferences from previous responses
        time.sleep(2)
        if sled_on:
            client.sendCommand('Lights On')
        if eyelink:
            eyetracker.stoprecording()

        mybutton = buttonpress(pref_button)
    	while mybutton.status:
            mybutton.check_buttons()

    def restart_experiment(self):
        if sled_on:
            client.sendCommand('Lights Off')