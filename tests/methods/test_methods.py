#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Florian
# Date: 18/01/2015

# Import libraries
import sys
import numpy as np
import json

from os.path import dirname, abspath, join

# Environmental settings
root_folder = dirname((abspath('__dir__')))
sys.path.append("{}/libs".format(root_folder))
from core.Core import Core
from core.Trial import Trial
import logging
import matplotlib.pyplot as plt
from core.methods.MethodContainer import MethodContainer
import time


def plot_staircase(intensities, responses, mu):
    """
    Plot intensities and responses for every trial
    :param intensities: list of intensities
    :type intensities: numpy array
    :param responses: list of responses ('True', 'False')
    :type responses: numpy array
    :param mu: list of true means
    """

    # Plot intensities
    plt.plot(intensities, '-')

    # Plot responses
    for i in range(intensities.shape[1]):
        if responses[:, i]:
            plt.plot(i, intensities[:, i], 'o')
        else:
            plt.plot(i, intensities[:, i], 'x')

    # Plot hidden state
    state = np.ones((1, intensities.shape[1])) * float(mu)
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



def plot_curve(intensities, response):
    """
    Plot psychometric curve
    :param intensities:
    :param response:
    :return:
    """
    # Bin intensities

    n_bins = 10
    bin_edges = np.linspace(np.min(intensities), np.max(intensities), n_bins)
    pY = np.zeros([1, n_bins])
    n = np.zeros([1, n_bins])

    for i in range(n_bins-1):
        idx = ((intensities >= bin_edges[i]) & (intensities < bin_edges[i+1]))
        pY[:, i] = np.sum(response[idx])/np.sum(idx)
        n[:, i] = np.sum(idx)

    idx = n > 0
    bin_edges = bin_edges[idx[0, :]]
    pY = pY[idx]

    fit(bin_edges, pY, n)


def fit(xdata, ydata, n):
    """
    Fit data
    :param xdata:
    :param ydata:
    :return:
    """
    from scipy.optimize import curve_fit

    def sigmoid(x, x0, k):
        y = 1 / (1 + np.exp(-k * (x - x0)))
        return y

    popt, pcov = curve_fit(sigmoid, xdata, ydata)

    x = np.linspace(np.min(xdata), np.max(xdata), 1000)
    y = sigmoid(x, *popt)

    dot_sizes = (n/float(np.max(n))) * 10
    for i in range(xdata.shape[0]):
        plt.plot(xdata[i], ydata[i], 'o', markersize=dot_sizes[:, i], label='data')

    plt.plot(x, y, label='fit')
    plt.ylim(-0.05, 1.05)
    plt.legend(loc='best')
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

    stairs = {}
    nSim = 10
    sd = 0.1 * (options['stimRange'][1] - options['stimRange'][0])  # std
    trues = np.random.uniform(options['stimRange'][0], options['stimRange'][1], (1, nSim)).flatten()
    estimates = []
    for s in range(nSim):

        responses = np.zeros([1, options['nTrials']])
        intensities = np.zeros([1, options['nTrials']])
        resp_curr = None
        intensity = None
        for t in range(options['nTrials']):
            init_time = time.time()
            intensity = Method.update(s, 1, load=False, response=str(resp_curr), intensity=intensity)
            stairs.update({str(s): {'true': trues[s]}})
            lapse_time = time.time() - init_time

            mu = trues[s]
            internal_rep = intensity + sd * np.random.normal()
            resp_curr = internal_rep > mu

            logging.info('ID: {0} mu: {1: 1.2f} sd: {2: 1.2f} intensity: {3: 1.2f} '
                         'internal: {4:1.2f} response: {5} [lapse: {6: 1.2f}s]'.format(
                            str(s), mu, sd, intensity, internal_rep, resp_curr, lapse_time))

            intensities[:, t] = intensity
            responses[:, t] = resp_curr

        if s == 1:
            plot_staircase(intensities, responses, trues[s])
            plot_curve(intensities, responses)

        estimates.append(intensities[:, -1])

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

    Exp.init(root_folder, conditions=conditions)

    # Instantiate Trial and experiment
    trial = Trial(design=Exp.design, settings=Exp.config.settings, userfile=Exp.user.datafilename)

    options = Exp.design.allconditions['options']
    Method = trial.method
    Method.options = options

    stairs = {}
    for t in Exp.design.design:
        if t['staircaseID'] not in stairs:
            stairs.update({str(t['staircaseID']): {'true': np.random.uniform(options['stimRange'][0],
                                                                             options['stimRange'][1])}})

    sd = 0.10 * (options['stimRange'][1] - options['stimRange'][0])  # std

    while trial.status is not False:
        trial.setup()

        if trial.status is True:
            intensity = Method.update(int(trial.parameters['staircaseID']), int(trial.parameters['staircaseDir']))

            mu = stairs[(trial.parameters['staircaseID'])]['true']

            internal_rep = intensity + sd * np.random.normal()
            resp_curr = internal_rep > mu

            logging.getLogger('EasyExp').info('ID: {} mu: {} intensity: {} internal: {} response: {}'.format(
                trial.parameters['staircaseID'], mu, intensity, internal_rep, resp_curr))

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

    ntrials = {}
    for trial in data:
        if trial['Replay'] == 'False':
            stair_id = trial['staircaseID']
            if stair_id not in res.keys():
                fields = copy.deepcopy(default_fields)
                res.update({stair_id: fields})
                res[stair_id]['id'] = stair_id
                ntrials[stair_id] = 0

            ntrials[stair_id] += 1
            res[stair_id]['intensities'].append(float(trial['intensity']))
            res[stair_id]['responses'].append(1 if trial['correct'] == "True" else 0)

    print('Completed trials per staircase:')
    print(ntrials)

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
    asa = {
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
                -70,
                70
            ],
            "maxInitialStepSize": 60.0,
            "stoppingStep": 0.1,
            "threshold": 0.50,
            "nTrials": 60,
            "limits": True,
            "nbStairs": 1,
            "warm_up": 2,
            "response_field": "correct",
            "intensity_field": "intensity"
        }
    }

    psi = {
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
              "nbStairs": 1,
              "warm_up": 0,
              "response_field": "correct",
              "intensity_field": "intensity"
            }
        }

    method_name = sys.argv[1] if len(sys.argv) > 1 else 'asa'
    if method_name == 'asa':
        conditions = asa
    elif method_name == 'psi':
        conditions = psi
    elif method_name == 'exp':
        # Get conditions file
        condition_name = sys.argv[2]
        path_to_conditions = join(root_folder, 'experiments', condition_name, 'conditions.json')
        json_info = open(path_to_conditions, 'r')
        conditions = json.load(json_info)
        json_info.close()
    else:
        raise Exception('Unknown method')

    run_simulation(method=conditions['method'], options=conditions['options'])

    run_easyexp_simulation(conditions=conditions)
