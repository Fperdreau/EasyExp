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
from core.methods.StaircaseASA.StaircaseASA import StaircaseASA


def main():
    """
    Main function: call experiment's routines
    """
    # New experiment
    Exp = Core()

    Exp.init(root_folder, custom=False)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config, userfile=Exp.user.datafilename)

    staircase = StaircaseASA(settings_file=Exp.files['conditions'], data_file=Exp.user.datafilename)

    stairs = {}
    while trial.status is not False:
        trial.setup()

        if trial.status is not False:
            intensity = staircase.update(int(trial.params['staircaseID']), int(trial.params['staircaseDir']))

            if trial.params['staircaseID'] not in stairs:
                stairs.update({trial.params['staircaseID']: {'true': np.random.uniform(-2.0, 2.0)}})

            mu = stairs[trial.params['staircaseID']]['true']
            sd = 0.1  # std

            internal_rep = intensity + sd * np.random.normal()
            resp_curr = internal_rep > mu

            print('ID: {} mu: {} intensity: {} internal: {} response: {}'.format(trial.params['staircaseID'], mu,
                                                                                 intensity, internal_rep, resp_curr))

            # Simulate lapse
            valid = np.random.uniform(0.0, 1.0) < 0.8
            trial.stop(valid)

            # Write data
            trial.writedata({'intensity': intensity, 'correct': resp_curr})

    # Load data from datafile
    data = trial.loadData()

    res = {}
    for trial in data:
        if trial['Replay'] == 'False':
            if trial['staircaseID'] not in res:
                res[trial['staircaseID']] = {'intensities': [], 'response': []}

            res[trial['staircaseID']]['intensities'].append(float(trial['intensity']))
            res[trial['staircaseID']]['response'].append(trial['correct'])

    # Plot staircase results
    import matplotlib.pyplot as plt

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
