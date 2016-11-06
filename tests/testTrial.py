#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian
# Date: 18/01/2015

# Import libraries
from os.path import dirname, abspath
import sys
import numpy as np

# Environmental settings
root_folder = dirname((abspath('__dir__')))
sys.path.append("{}/libs".format(root_folder))
from core.Core import Core
from core.Trial import Trial
from core.methods.PsiMarginal.PsiMarginal import PsiMarginal


def main():
    """
    Main function: call experiment's routines
    """

    # New experiment
    Exp = Core()

    Exp.init(root_folder, custom=False)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config.settings, userfile=Exp.user.datafilename,
                  pause_interval=int(Exp.config.settings['setup']['pauseInt']))

    while trial.status is not False:
        trial.setup()

        if trial.status is True:

            valid = np.random.uniform(0.0, 1.0) < 0.95
            trial.stop(valid)
            trial.write_data({'intensity': 0, 'correct': 'left'})

    data = trial.load_data()

    # Check that all the conditions have been played
    levels = Exp.design.allconditions['timing']
    trials_per_condition = np.zeros((1, len(levels)))
    for row in data:
        if row['Replay'] == 'False':
            ind = [i for i, j in enumerate(levels) if j == float(row['timing'])]
            trials_per_condition[0, ind[0]] += 1
    print(trials_per_condition)

if __name__ == '__main__':
    main()
