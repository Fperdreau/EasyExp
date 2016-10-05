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
import logging


def main():
    """
    Main function: call experiment's routines
    """
    options = {
        'stimRange': (-3.0, 3.0, 0.5),  # Boundaries of stimulus range
        'Pfunction': 'cGauss',  # Underlying Psychometric function
        'nTrials': 20,  # Number of trials per staircase
        'threshold': (-3.0, 3.0, 0.01),  # Threshold estimate
        'thresholdPrior': ('uniform',),  # Prior on threshold
        'slope': (0.005, 10, 0.1),  # Slope estimate and prior
        'slopePrior': ('uniform',),  # Prior on slope
        'guessRate': (0.0, 0.11, 0.01),  # Guess-rate estimate and prior
        'guessPrior': ('uniform',),  # Prior on guess rate
        'lapseRate': (0.0, 0.11, 0.01),  # Lapse-rate estimate and prior
        'lapsePrior': ('uniform',),  # Prior on lapse rate
        'marginalize': True,  # Marginalize out the nuisance parameters guess rate and lapse rate?
        'nbStairs': 1,  # Number of staircase per condition
        'warm_up': 2,  # Number of warm-up trials per staircase (only extreme intensities)
        'response_field': 'correct',  # Name of response field in data file
        'intensity_field': 'intensity'  # Name of intensity field in data file
    }

    # New experiment
    Exp = Core()

    Exp.init(root_folder, custom=False)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config, userfile=Exp.user.datafilename)

    staircase = PsiMarginal(settings_file=Exp.files['conditions'], data_file=Exp.user.datafilename, options=options)

    run = False
    if run:
        stairs = {}
        while trial.status is not False:
            trial.setup()

            if trial.status is not False:
                intensity = staircase.intensity

                if trial.params['staircaseID'] not in stairs:
                    stairs.update({trial.params['staircaseID']: {'true': np.random.uniform(-2.0, 2.0)}})

                mu = stairs[trial.params['staircaseID']]['true']
                sd = 0.1  # std

                internal_rep = intensity + sd * np.random.normal()
                resp_curr = internal_rep > mu

                logging.getLogger('EasyExp').info('ID: {} mu: {} intensity: {} internal: {} response: {}'.format(
                    trial.params['staircaseID'], mu, intensity, internal_rep, resp_curr))

                # Simulate lapse
                valid = np.random.uniform(0.0, 1.0) < 0.8
                trial.stop(valid)

                # Write data
                trial.writedata({'intensity': intensity, 'correct': resp_curr})
                staircase.update(int(trial.params['staircaseID']), int(trial.params['staircaseDir']))

    # Load data from datafile
    data = trial.loadData()

    # Analysis
    import pandas as pd
    import pprint
    # Plot staircase results
    import matplotlib.pyplot as plt

    res = {}
    default_fields = {
        'intensities': [],
        'response': [],
        'n': [],
        'bin_intensities': [],
        'bin_responses': []
    }

    # data = pd.DataFrame(data)
    # subdata = data[data.Replay != 'False', :]

    for trial in data:
        if trial['Replay'] == 'False':
            if trial['staircaseID'] not in res:
                res[trial['staircaseID']] = default_fields

            res[trial['staircaseID']]['intensities'].append(float(trial['intensity']))
            res[trial['staircaseID']]['response'].append(1 if trial['correct'] == "True" else 0)

    for ind, stair in res.iteritems():
        pprint.pprint(stair)
        bins = np.linspace(min(stair['intensities']), max(stair['intensities']), 10)
        [n, x] = np.histogram(stair['intensities'], bins)
        indices = np.digitize(stair['intensities'], bins)
        stair['response'] = np.array(stair['response'])
        print(n, indices)
        stair['bin_responses'] = np.zeros((1, len(bins)))
        stair['n'] = n
        for b in range(1, len(bins)):
            total_correct = np.sum(stair['response'][indices == b])
            stair['bin_responses'][b] = total_correct / stair['n'][b-1]
        stair['bin_intensities'] = bins

        # Plot responses
        markersize = (stair['n'] / float(np.max(stair['n']))) * 20
        for i in range(len(stair['bin_responses'])):
            plt.plot(i, stair['bin_responses'][i], 'o', markersize=markersize[i])

    trues = []
    estimates = []
    for stair, result in res.iteritems():
        intensities = result['intensities']
        responses = result['response']
        stairs[stair]['estimate'] = intensities[-1]
        trues.append(stairs[stair]['true'])
        estimates.append(stairs[stair]['estimate'])

        # Plot intensities
        plt.plot(intensities)

        # Plot responses
        for i in range(len(intensities)):
            if responses[i] == 'True':
                plt.plot(i, intensities[i], 'o')
            else:
                plt.plot(i, intensities[i], 'x')

        # Plot hidden state
        state = np.ones((1, len(intensities))) * float(stairs[stair]['true'])
        plt.plot(state[0], '--')
    plt.show()
    plt.xlabel('Trial')
    plt.ylabel('Stimulus intensity')

    plt.scatter(trues, estimates)
    plt.xlabel('True mean')
    plt.ylabel('Estimates')
    plt.show()

    # Check that all the conditions have been played
    levels = Exp.design.allconditions['timing']
    nProbe = np.zeros((1, len(levels)))
    for row in data:
        if row['Replay'] == 'False':
            ind = [i for i, j in enumerate(levels) if j == float(row['timing'])]
            nProbe[0, ind[0]] += 1
    print(nProbe)

if __name__ == '__main__':
    main()
