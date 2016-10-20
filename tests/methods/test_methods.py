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
import matplotlib.pyplot as plt
from core.methods.MethodContainer import MethodContainer


def plot_staircase(intensities, responses, mu):
    """
    Plot intensities and responses for every trial
    :param intensities: list of intensities
    :type intensities: array-like
    :param responses: list of responses ('True', 'False')
    :type responses: (str, str)
    :param mu: list of true means
    """

    # Plot intensities
    plt.plot(intensities)

    # Plot responses
    for i in range(len(intensities)):
        if responses[i] == 'True':
            plt.plot(i, intensities[i], 'o')
        else:
            plt.plot(i, intensities[i], 'x')

    # Plot hidden state
    state = np.ones((1, len(intensities))) * float(mu)
    plt.plot(state[0], '--')
    plt.xlabel('Trial')
    plt.ylabel('Stimulus intensity')
    plt.show()


def plot_correlation(trues, estimates):
    """
    Plot estimates as a function of true mean
    :param trues:
    :param estimates:
    :return:
    """
    plt.scatter(trues, estimates)
    plt.xlabel('True mean')
    plt.ylabel('Estimates')
    plt.show()


def run_simulation(options, method):
    """
    Run simulations without using EasyExp (faster)
    :param options:
    :param method:
    :return:
    """
    logging.basicConfig(level=logging.DEBUG)

    Method = MethodContainer(method=method, options=options)

    run = True
    if run:
        stairs = {}
        nSim = 10
        sd = 0.1  # std
        trues = np.random.uniform(options['stimRange'][0], options['stimRange'][1], (1, nSim)).flatten()
        estimates = []
        for s in range(nSim):

            responses = []
            intensities = []
            resp_curr = None
            intensity = None
            for t in range(options['nTrials']):
                intensity = Method.update(s, 1, load=False, response=str(resp_curr), intensity=intensity)
                stairs.update({str(s): {'true': trues[s]}})

                mu = trues[s]
                internal_rep = intensity + sd * np.random.normal()
                resp_curr = internal_rep > mu

                logging.info('ID: {} mu: {} intensity: {} internal: {} response: {}'.format(
                    str(s), mu, intensity, internal_rep, resp_curr))

                intensities.append(intensity)
                responses.append(resp_curr)

            responses = ['True' if i == True else 'False' for i in responses]

            plot_staircase(intensities, responses, trues[s])

            estimates.append(intensities[-1])

        plot_correlation(trues, estimates)


def run_easyexp_simulation(conditions=None):
    """
    Run simulation using the EasyExp framework
    :param conditions: dictionary providing experiment conditions. If not provided, then conditions.json will be loaded
    :type conditions: dict
    :return:
    """
    # New experiment
    Exp = Core()

    Exp.init(root_folder, custom=False, conditions=conditions)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config, userfile=Exp.user.datafilename)

    options = Exp.design.allconditions['options']
    Method = trial.method
    Method.options = options

    stairs = {}
    for t in Exp.design.design:
        if t['staircaseID'] not in stairs:
            stairs.update({str(t['staircaseID']): {'true': np.random.uniform(options['stimRange'][0],
                                                                             options['stimRange'][1])}})

    while trial.status is not False:
        trial.setup()

        if trial.status is not False:
            intensity = Method.update(int(trial.params['staircaseID']), int(trial.params['staircaseDir']))

            mu = stairs[(trial.params['staircaseID'])]['true']
            sd = 0.1  # std

            internal_rep = intensity + sd * np.random.normal()
            resp_curr = internal_rep > mu

            logging.getLogger('EasyExp').info('ID: {} mu: {} intensity: {} internal: {} response: {}'.format(
                trial.params['staircaseID'], mu, intensity, internal_rep, resp_curr))

            # Simulate lapse
            valid = np.random.uniform(0.0, 1.0) <= 1.0
            trial.stop(valid)

            # Write data
            trial.write_data({'intensity': intensity, 'correct': resp_curr})

    # Load data from datafile
    data = trial.load_data()

    # Analysis
    # Plot staircase results
    import copy
    res = dict()
    default_fields = {
        'id': None,
        'intensities': [],
        'responses': [],
        'n': [],
        'bin_intensities': [],
        'bin_responses': []
    }

    for trial in data:
        if trial['Replay'] == 'False':
            stair_id = trial['staircaseID']
            if stair_id not in res.keys():
                fields = copy.deepcopy(default_fields)
                res.update({stair_id: fields})
                res[stair_id]['id'] = stair_id

            res[stair_id]['intensities'].append(float(trial['intensity']))
            res[stair_id]['responses'].append(1 if trial['correct'] == "True" else 0)

    for ind in res.keys():
        stair = res[ind]
        bins = np.linspace(min(stair['intensities']), max(stair['intensities']), 10)
        indices = np.digitize(stair['intensities'], bins)
        stair['responses'] = np.array(stair['responses'])
        stair['bin_responses'] = np.zeros((1, len(bins)))
        stair['n'] = np.zeros((1, len(bins)))
        for b in range(1, len(bins)):
            stair['n'][0, b-1] = len(stair['responses'][indices == b])
            total_correct = np.sum(stair['responses'][indices == b])
            stair['bin_responses'][0, b-1] = (total_correct / float(stair['n'][0, b-1])) if stair['n'][0, b-1] > 0 else 0.0
        stair['bin_intensities'] = bins

    # Plot responses
    marker_size = (stair['n'][0, :] / float(np.max(stair['n'][0, :]))) * 20
    for i in range(len(bins)):
        plt.plot(bins[i], stair['bin_responses'][0, i], 'o', markersize=marker_size[i])

    plt.xlabel('Stimulus intensity')
    plt.ylabel('p(correct)')
    plt.show()

    trues = []
    estimates = []
    for stair, result in res.iteritems():
        intensities = result['intensities']
        responses = result['responses']
        stairs[stair]['estimate'] = intensities[-1]
        trues.append(stairs[stair]['true'])
        estimates.append(stairs[stair]['estimate'])
        responses = ['True' if i == True else 'False' for i in responses]

        plot_staircase(intensities, responses, stairs[stair]['true'])

    plot_correlation(trues, estimates)


if __name__ == '__main__':
    conditions_ASA = {
        "timing": [
            1,
            2,
            3,
            4,
            5
        ],
        "repetition": 1,
        "method": "StaircaseASA",
        "options": {
            "stimRange": [
                -2.8,
                2.8
            ],
            "maxInitialStepSize": 3.0,
            "stoppingStep": 0.1,
            "threshold": 0.50,
            "nTrials": 40,
            "limits": True,
            "nbStairs": 1,
            "warm_up": 2,
            "response_field": "correct",
            "intensity_field": "intensity"
        }
    }

    conditions_psi = {
          "conditions": [
            1,
            2,
            3,
            4,
            5
          ],
          "repetition": 1,
          "method": "PsiMarginal",
          "options": {
              "stimRange": [-5.0, 5.0, 1],
              "Pfunction": "cGauss",
              "nTrials": 40,
              "threshold": [-10, 10, 0.1],
              "thresholdPrior": ["uniform", None],
              "slope": [0.005, 20, 0.1],
              "slopePrior": ["uniform", None],
              "guessRate": [0.0, 0.11, 0.05],
              "guessPrior": ["uniform", None],
              "lapseRate": [0.0, 0.11, 0.05],
              "lapsePrior": ["uniform", None],
              "marginalize": True,
              "nbStairs": 2,
              "warm_up": 5,
              "response_field": "correct",
              "intensity_field": "intensity"
            }
        }

    conditions = conditions_psi

    run_simulation(method=conditions['method'], options=conditions['options'])

    run_easyexp_simulation(conditions=conditions)
