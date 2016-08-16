#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian Perdreau
# Date: 18/01/2015

import OpenGL
import sys
import time

OpenGL.ERROR_ON_COPY = True  # make sure we send numpy arrays
import signal

# PyQt
# PyQt (package python-qt4-gl on Ubuntu)
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtOpenGL import *

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


class QtWindow(QMainWindow):
    """
    Open a QT window
    """

    def __init__(self, screen=object, experiment=object):
        """
        Class constructor
        :param Screen screen: instantiation of Screen class
        :param RunTrial experiment: instantiation of RunTrial class
        :return:
        """
        super(QtWindow, self).__init__()
        self.screen = screen
        self.QTapp = screen.QTapp
        self.experiment = experiment

        self.central_widget = None
        self.widget = None
        self.fullscreen = False

        self.status = 'idle'
        self.timer = time.time()
        self.paused = True

        # Import GUI
        self.initUI()

    def __del__(self):
        self.quit()

    def quit(self):
        self.QTapp.quit()

    def setwidget(self, widget):
        self.central_widget = widget
        self.central_widget.setObjectName(_fromUtf8("central_widget"))
        self.setCentralWidget(self.central_widget)

    def removewidget(self):
        self.central_widget.setParent(None)

    def initUI(self):
        # General settings
        self.fullscreen = self.screen.fullscreen
        self.setObjectName(_fromUtf8("MainWindow"))
        self.setMinimumSize(self.screen.width_px, self.screen.height_px)
        self.resize(self.screen.width_px, self.screen.height_px)
        self.setWindowTitle(QApplication.translate(self.screen.expname, self.screen.expname, None,
                                                   QApplication.UnicodeUTF8))

        # dialogs
        self.errorMessageDialog = QErrorMessage(self)

        # Menu & Actions
        self.create_actions()
        self.create_menus()

        self.statusBar().showMessage('Ready')
        self.run_home()
        self.show()

    def create_actions(self):
        """
        Define actions and shortcuts
        :return:
        """
        self.startIcon = QIcon('icon/start.png')
        self.stopIcon = QIcon('icon/pause.png')
        calIcon = QIcon('icon/cal.png')
        quitIcon = QIcon('icon/quit.png')
        fullIcon = QIcon('icon/full.png')

        # Start/Stop Experiment
        self.startAction = QAction(self.startIcon, '&Start/Stop', self)
        self.startAction.setShortcut('Ctrl+R')
        self.startAction.setStatusTip('Start/Stop')
        self.startAction.triggered.connect(self.startStop)

        # Quit application
        self.exitAction = QAction(quitIcon, '&Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Quit application')
        self.exitAction.triggered.connect(self.quit)

        # Trigger fullscreen mode
        self.fullAction = QAction(fullIcon, '&Full Screen', self)
        self.fullAction.setShortcut('Ctrl+F')
        self.fullAction.setStatusTip('Toggle Full Screen')
        self.fullAction.triggered.connect(self.toggleFullScreen)

    def create_menus(self):
        """
        Create Menu bar
        :return:
        """
        # populate the menu bar
        menubar = self.menuBar()
        self.experimentMenu = menubar.addMenu('&Experiment')
        self.experimentMenu.addAction(self.startAction)
        self.experimentMenu.addAction(self.exitAction)

        # View Menu
        viewMenu = menubar.addMenu('&View')
        viewMenu.addAction(self.fullAction)

        self.addAction(self.startAction)
        self.addAction(self.fullAction)
        self.addAction(self.exitAction)

    def startStop(self):
        """
        Start/Stop the experiment
        :return:
        """
        if self.status == 'running':
            self.status = 'idle'
            self.startAction.setIcon(self.startIcon)
            self.stop_exp()
            self.statusBar().showMessage('Idle')
        elif self.status == 'idle':
            self.status = 'running'
            self.start_exp()
            self.startAction.setIcon(self.stopIcon)
            self.statusBar().showMessage('Running')

    def toggleFullScreen(self):
        """
        Toggle Fullscreen mode
        :return:
        """
        if self.isFullScreen():
            self.showNormal()
            self.menuBar().setVisible(True)
            self.statusBar().setVisible(True)
            self.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self.showFullScreen()
            self.menuBar().setVisible(False)
            self.statusBar().setVisible(False)
            self.setCursor(QCursor(Qt.BlankCursor))

    def toggleText(self, text, align='center', color='#FFFFFF', bgcol='#000000', fontsize='150', font='Arial'):
        """
        Display a text
        :param text: Text to display
        :param align: Text horizontal alignment
        :param color: Text color in Hex (e.g.: #000000)
        :param bgcol: Background color in Hex (e.g.: #FFFFFF)
        :param fontsize: Font size in Pt
        :param font: Font family (e.g.: Arial)
        """
        textQ = QLabel(text)
        style = 'text-align: {}; color: {}; background-color:{}; font-size: {}; font-family: {};'\
            .format(align, color, bgcol, fontsize, font)
        textQ.setStyleSheet(style)
        self.setwidget(textQ)

    def run_home(self):
        """
        Call Home widget (just a welcome message)
        """
        self.status = 'idle'
        text = 'Hello and Thank you for participating in this experiment!'
        self.toggleText(text)

    def setExperiment(self, experiment):
        """
        Set experiment
        :param experiment:
        """
        self.experiment = experiment

    def start_exp(self):
        """
        Start the experiment and run the timer
        """
        self.timer = time.time()
        self.experiment.state = 'home'
        self.experiment.changestate()
        self.setwidget(self.experiment)
        self.status = 'running'

    def gonext(self):
        """
        Go to next state by pressing SPACE
        """
        try:
            self.central_widget.gonext()
        except Exception as e:
            print 'GO next: {}'.format(e)

    def stop_exp(self):
        """
        Stop the experiment and stop the timer
        """
        self.central_widget.quit()
        self.central_widget.destroy(True, True)
        self.run_home()
        duration = round((time.time() - self.timer)/60)
        print "\n--- End of Experiment '{}' ---" \
              "\nTotal duration: {} minutes" \
              "\n---\n"\
              .format(self.screen.expname, duration)