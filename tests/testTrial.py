#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian
# Date: 18/01/2015

# Import libraries
from os.path import dirname, abspath
import sys
import numpy as np

# Environmental settings
root_folder = dirname(dirname(abspath('__dir__')))
sys.path.append("{}/libs".format(root_folder))
from core.Core import Core
from core.Trial import Trial
from core.methods.PsiMarginal.PsiMarginal import PsiMarginal


def main():
    """
    Main function: call experiment's routines
    """
    options = {
        'stimRange': (-2.8, 2.8),                    # Boundaries of stimulus range
        'Pfunction': 'cGauss',                  # Underlying Psychometric function
        'nTrials': 50,                          # Number of trials per staircase
        'threshold': np.linspace(-2.8, 2.8, 20),                      # Threshold estimate
        'thresholdPrior': ('uniform', None),    # Prior on threshold
        'slope':  np.logspace(-3.0, 3.0, 20),                          # Slope estimate
        'slopePrior': ('uniform', None),        # Prior on slope
        'guessRate': np.linspace(0.40, 0.60, 20),                      # Guess-rate estimate
        'guessPrior': ('uniform', None),        # Prior on Guess-rate
        'lapseRate': np.linspace(0.0, 0.05, 20),                      # Lapse-rate estimate
        'lapsePrior': ('uniform', None),        # Prior on lapse-rate
        'marginalize': True,                    #
        'nbStairs': 1,                          # Number of staircase per condition
        "warm_up": 4,                           # Number of warm-up trials per staircase (only extremes intensity)
        "response_field": "response",           # Name of response field in data file
        "intensity_field": "intensity"          # Name of intensity field in data file
    }

    print(root_folder)
    # New experiment
    Exp = Core()

    Exp.init(root_folder, custom=False)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config, userfile=Exp.user.datafilename,
                  pause_interval=int(Exp.config['pauseInt']))

    # staircase = StairCaseASA(settings_file=Exp.files['conditions'], data_file=Exp.user.datafilename)
    staircase = PsiMarginal(settings_file=Exp.files['conditions'], data_file=Exp.user.datafilename, options=options)
    stairs = {}
    while trial.status is not False:
        trial.setup()

        if trial.status is not False:
            intensity = staircase.update(int(trial.params['staircaseID']), int(trial.params['staircaseDir']))
            print('intensity: {}'.format(intensity))
            if trial.params['staircaseID'] not in stairs:
                stairs.update({trial.params['staircaseID']: {'true': np.random.uniform(-2.0, 2.0)}})

            mu = stairs[trial.params['staircaseID']]['true']
            sd = 0.1  # std
            internal_rep = intensity + sd * np.random.normal()
            resp_curr = (abs(internal_rep) > abs(mu))
            print('ID: {} mu: {} internal: {} response: {} noise: {}'.format(trial.params['staircaseID'], mu,
                  internal_rep, resp_curr, np.random.normal()*sd))
            valid = np.random.uniform(0.0, 1.0) < 0.8
            trial.stop(valid)
            trial.write_data({'intensity': intensity, 'correct': resp_curr})

    data = trial.load_data()

    res = {}
    for trial in data:
        if trial['Replay'] == 'False':
            if trial['staircaseID'] not in res:
                res[trial['staircaseID']] = []

            res[trial['staircaseID']].append(float(trial['intensity']))

    # Plot staircase results
    import matplotlib.pyplot as plt
    trues = []
    estimates = []
    for stair, intensities in res.iteritems():
        stairs[stair]['estimate'] = intensities[len(intensities)-1]
        trues.append(stairs[stair]['true'])
        estimates.append(stairs[stair]['estimate'])
        plt.plot(intensities)
    plt.show()

    plt.scatter(trues, estimates)
    plt.xlabel('True mean')
    plt.ylabel('Estimates')
    plt.show()

    from pprint import pprint
    pprint(stairs)

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
