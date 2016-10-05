# -*- coding: utf-8 -*-
"""
Copyright © 2016, N. Niehof, Radboud University Nijmegen

PsiMarginal is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PsiMarginal is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PsiMarginal. If not, see <http://www.gnu.org/licenses/>.

---

Psi adaptive staircase procedure for use in psychophysics, as described in Kontsevich & Tyler (1999)
and psi-marginal staircase as described in Prins(2013). Implementation based on the psi-marginal method
in the Palamedes toolbox (version 1.8.1) for Matlab.

References:

Kontsevich, L. L. & Tyler, C. W. (1999). Bayesian adaptive estimation of psychometric slope and threshold.
    Vision Research, 39, 2729-2737.
Prins, N & Kingdom, F. A. A. (2009). Palamedes: Matlab routines for analyzing psychophysical data.
    http://www.palamedestoolbox.org 
Prins, N. (2013). The psi-marginal adaptive method: How to give nuisance parameters the attention they
    deserve (no more, no less). Journal of Vision, 13(7):3, 1-17.
"""

import numpy as np
from os.path import isfile

# Import Base class
import time

from ..MethodBase import MethodBase

# Data I/O
import json
import csv

from sklearn.utils.extmath import cartesian
from scipy.stats import norm
from scipy.special import erfc
import logging


def PF(parameters, psyfun='cGauss'):
    """Generate conditional probabilities from psychometric function.
    
    Arguments
    ---------
    :param parameters: ndarray containing parameters as columns
            alpha   : threshold

            beta    : slope

            gamma   : guessing rate (optional), default is 0.2

            lambda  : lapse rate (optional), default is 0.04

            x       : stimulus intensity
    :type parameters: [alpha, beta, lambda, x]

    :param psyfun: type of psychometric function.
            'cGauss' cumulative Gaussian

            'Gumbel' Gumbel, aka log Weibull
    :type psyfun: str

    Returns
    -------
    1D-array of conditional probabilities p(response | alpha,beta,gamma,lambda,x)
    """

    # Unpack parameters
    if np.size(parameters, 1) == 5:
        [alpha, beta, gamma, llambda, x] = np.transpose(parameters)
    elif np.size(parameters, 1) == 4:
        [alpha, beta, llambda, x] = np.transpose(parameters)
        gamma = llambda
    elif np.size(parameters, 1) == 3:
        [alpha, beta, x] = np.transpose(parameters)
        gamma = 0.2
        llambda = 0.04
    else:  # insufficient number of parameters will give a flat line
        psyfun = None
        gamma = 0.2
        llambda = 0.04
    
    # Psychometric function
    ones = np.ones(np.shape(alpha))
    if psyfun == 'cGauss':
        # F(x; alpha, beta) = Normcdf(alpha, beta) = 1/2 * erfc(-beta * (x-alpha) /sqrt(2))
        pf = ones/2 * erfc(np.multiply(-beta, (np.subtract(x, alpha))) /np.sqrt(2))
    elif psyfun == 'Gumbel':
        # F(x; alpha, beta) = 1 - exp(-10^(beta(x-alpha)))
        pf = ones - np.exp(-np.power((np.multiply(ones,10.0)), (np.multiply(beta, (np.subtract(x, alpha))))))
    else:
        # flat line if no psychometric function is specified
        pf = np.ones(np.shape(alpha))
    y = gamma + np.multiply((ones - gamma - llambda), pf)
    return y


class PsiMarginal(MethodBase):
    """
    Find the stimulus intensity with minimum expected entropy for each trial, to determine the psychometric function.
  
    Psi adaptive staircase procedure for use in psychophysics.   
    
    Arguments
    ---------
        stimRange :
            range of possible stimulus intensities.

        Pfunction (str) : type of psychometric function to use.
            'cGauss' cumulative Gaussian
            
            'Gumbel' Gumbel, aka log Weibull
        
        nTrials :
            number of trials
            
        threshold :
            (alpha) range of possible threshold values to search
            
        thresholdPrior (tuple) : type of prior probability distribution to use.
            Also: slopePrior, guessPrior, lapsePrior.
            
            ('normal',0,1): normal distribution, mean and standard deviation.
            
            ('uniform',None) : uniform distribution, mean and standard deviation not defined.
            
        slope :
            (beta) range of possible slope values to search
        
        slopePrior :
            see thresholdPrior
            
        guessRate :
            (gamma) range of possible guessing rate values to search
        
        guessPrior :
            see thresholdPrior
        
        lapseRate :
            (lambda) range of possible lapse rate values to search
        
        lapsePrior :
            see thresholdPrior
        
        marginalize (bool) :
            If True, marginalize out the lapse rate and guessing rate before finding the stimulus
            intensity of lowest expected entropy. This uses the Prins (2013) method to include the guessing and lapse rate
            into the probability distribution. These rates are then marginalized out, and only the threshold and slope are included
            in selection of the stimulus intensity.
            
            If False, lapse rate and guess rate are included in the selection of stimulus intensity.
    
    How to use
    ----------
        Create a psi object instance with all relevant arguments. Selecting a correct search space for the threshold,
        slope, guessing rate and lapse rate is important for the psi procedure to function well. If an estimate for
        one of the parameters ends up at its (upper or lower) limit, the result is not reliable, and the procedure
        should be repeated with a larger search range for that parameter.
        
        Example:
            >>> s   = range(-5,5) # possible stimulus intensities
            obj = Psi(s)
        
        The stimulus intensity to be used in the current trial can be found in the field intensity.
        
        Example:
            >>> stim = obj.intensity
        
        After each trial, update the psi staircase with the subject response, by calling the addData method.
        
        Example:
            >>> obj.addData(resp)
    """

    # Default options
    _options = {
        'stimRange': (-5, 5, 0.1),  # Boundaries of stimulus range
        'Pfunction': 'cGauss',  # Underlying Psychometric function
        'nTrials': 50,  # Number of trials per staircase
        'threshold': (-10, 10, 0.1),  # Threshold estimate
        'thresholdPrior': ('uniform',),  # Prior on threshold
        'slope': (0.005, 10, 0.1),  # Slope estimate and prior
        'slopePrior': ('uniform',),  # Prior on slope
        'guessRate': (0.0, 0.11, 0.01),  # Guess-rate estimate and prior
        'guessPrior': ('uniform',),  # Prior on guess rate
        'lapseRate': (0.0, 0.11, 0.01),  # Lapse-rate estimate and prior
        'lapsePrior': ('uniform',),  # Prior on lapse rate
        'marginalize': True,  # Marginalize out the nuisance parameters guess rate and lapse rate?
        'nbStairs': 1,  # Number of staircase per condition
        'warm_up': 4,  # Number of warm-up trials per staircase (only extreme intensities)
        'response_field': 'response',  # Name of response field in data file
        'intensity_field': 'intensity'  # Name of intensity field in data file
    }

    def __init__(self, settings_file=None, data_file=None, options=None):
        """
        Psi constructor
        
        Parameters
        ----------
        :param options : dictionary providing staircase settings
        :type options: dict
        :param settings_file: full path to settings (json) file
        :type settings_file: str
        :param data_file: full path to data file
        :type data_file: str
        """
        self.data = None
        self._settings_file = settings_file
        self._data_file = data_file

        # Load staircase settings from file
        self._load_options(options)

        # Psychometric function parameters
        list_ranges = ('threshold', 'slope', 'guessRate', 'lapseRate')
        self.ranges = dict()
        for opt in list_ranges:
            self.ranges[opt] = np.arange(self._options[opt][0], self._options[opt][1], self._options[opt][2])

        self.stimRange = np.arange(float(self._options['stimRange'][0]), float(self._options['stimRange'][1]),
                                   float(self._options['stimRange'][2]))
        self.marginalize = self._options['marginalize']
        self.threshold = self.ranges['threshold']
        self.slope = self.ranges['slope']
        self.guessRate = self.ranges['guessRate']
        self.lapseRate = self.ranges['lapseRate']

        # remove any singleton dimensions
        self.threshold = np.squeeze(self.threshold)
        self.slope = np.squeeze(self.slope)
        self.guessRate = np.squeeze(self.guessRate)
        self.lapseRate = np.squeeze(self.lapseRate)

        logging.getLogger('EasyExp').info('threshold: {}'.format(self.threshold))
        logging.getLogger('EasyExp').info('slope: {}'.format(self.slope))
        logging.getLogger('EasyExp').info('guessRate: {}'.format(self.guessRate))
        logging.getLogger('EasyExp').info('lapse: {}'.format(self.lapseRate))

        # Priors
        self.priorAlpha = self.__genprior(self.threshold, *self._options['thresholdPrior'])
        self.priorBeta = self.__genprior(self.slope, *self._options['slopePrior'])
        self.priorGamma = self.__genprior(self.guessRate, *self._options['guessPrior'])
        self.priorLambda = self.__genprior(self.lapseRate, *self._options['lapsePrior'])
        
        # if guess rate equals lapse rate, and they have equal priors,
        # then gamma can be left out, as the distributions will be the same
        self.gammaEQlambda = all([[all(self.guessRate == self.lapseRate)], [all(self.priorGamma == self.priorLambda)]])
        
        # likelihood: table of conditional probabilities p(response | alpha,beta,gamma,lambda,x)
        # prior: prior probability over all parameters p_0(alpha,beta,gamma,lambda)
        if self.gammaEQlambda:
            self.dimensions = (len(self.threshold), len(self.slope), len(self.lapseRate), len(self.stimRange))
            self.parameters = cartesian((self.threshold, self.slope, self.lapseRate, self.stimRange))   
            self.likelihood = PF(self.parameters, psyfun=self._options['Pfunction'])
            self.likelihood = np.reshape(self.likelihood, self.dimensions) # dims: (alpha, beta, lambda, x)
            self.pr = cartesian((self.priorAlpha, self.priorBeta, self.priorLambda))
            self.prior = np.prod(self.pr, axis=1) # row-wise products of prior probabilities
            self.prior = np.reshape(self.prior, self.dimensions[:-1]) # dims: (alpha, beta, lambda)
        else:
            self.dimensions = (len(self.threshold), len(self.slope), len(self.guessRate),
                               len(self.lapseRate), len(self._options['stimRange']))
            self.parameters = cartesian((self.threshold, self.slope, self.guessRate, self.lapseRate, self.stimRange))   
            self.likelihood = PF(self.parameters, psyfun=self._options['Pfunction'])
            self.likelihood = np.reshape(self.likelihood, self.dimensions) # dims: (alpha, beta, gamma, lambda, x)
            self.pr = cartesian((self.priorAlpha, self.priorBeta, self.priorGamma, self.priorLambda))
            self.prior = np.prod(self.pr, axis=1) # row-wise products of prior probabilities
            self.prior = np.reshape(self.prior, self.dimensions[:-1]) # dims: (alpha, beta, gamma, lambda)
        
        # normalize prior
        self.prior = self.prior / np.sum(self.prior)

        # Set probability density function to prior
        self.pdf = np.copy(self.prior)

        # settings
        self.iTrial = 0
        self.nTrials = self._options['nTrials']
        self.stop = 0
        self.response = []

        self.resp_list = np.zeros(())
        self.int_list = np.zeros(())
        self.intensity = None

        # Settings (expFrame)
        self.cpt_stair = 0

        # Generate the first stimulus intensity
        self.minEntropyStim()

    def __genprior(self, x, distr='uniform', mu=0, sig=1): # prior probability distribution
        if distr == 'uniform':
            nx = len(x)
            p = np.ones(nx)/nx
        elif distr == 'normal':
            p = norm.pdf(x, mu, sig)
        else:
            nx = len(x)
            p = np.ones(nx)/nx
        return p

    def __entropy(self, pdf):  # Shannon entropy of probability density function
        # Marginalize out all nuisance parameters, i.e. all except alpha and beta
        postDims = np.ndim(pdf)
        if self.marginalize:
            while postDims > 3:  # marginalize out second-to-last dimension, last dim is x
                pdf = np.sum(pdf, axis=-2)
                postDims -= 1
        # find expected entropy, suppress divide-by-zero and invalid value warnings
        # as this is handled by the NaN redefinition to 0
        with np.errstate(divide='ignore', invalid='ignore'):
            entropy = np.multiply(pdf, np.log(pdf))
        entropy[np.isnan(entropy)] = 0  # define 0*log(0) to equal 0
        dimSum = tuple(range(postDims-1))  # dimensions to sum over. also a Chinese dish
        entropy = -(np.sum(entropy, axis=dimSum))
        return entropy

    def minEntropyStim(self):
        """
        Find the stimulus intensity based on the expected information gain.
        
        Minimum Shannon entropy is used as selection criterion for the stimulus intensity in the upcoming trial.
        """
        self.pdf = self.pdf
        self.nX = len(self.stimRange)
        self.nDims = np.ndim(self.pdf)

        # make pdf the same dims as conditional prob table likelihood
        self.pdfND = np.expand_dims(self.pdf, axis=self.nDims)  # append new axis
        self.pdfND = np.tile(self.pdfND, self.nX)  # tile along new axis
        
        # Probabilities of response r (success, failure) after presenting a stimulus
        # with stimulus intensity x at the next trial, multiplied with the prior (pdfND)
        self.pTplus1success = np.multiply(self.likelihood, self.pdfND)
        self.pTplus1failure = self.pdfND - self.pTplus1success
        
        # Probability of success or failure given stimulus intensity x, p(r|x)
        self.sumAxes = tuple(range(self.nDims))  # sum over all axes except the stimulus intensity axis
        self.pSuccessGivenx = np.sum(self.pTplus1success, axis=self.sumAxes)
        self.pFailureGivenx = np.sum(self.pTplus1failure, axis=self.sumAxes)
        
        # Posterior probability of parameter values given stimulus intensity x and response r
        # p(alpha, beta | x, r)
        self.posteriorTplus1success = self.pTplus1success / self.pSuccessGivenx
        self.posteriorTplus1failure = self.pTplus1failure / self.pFailureGivenx
        
        # Expected entropy for the next trial at intensity x, producing response r
        self.entropySuccess = self.__entropy(self.posteriorTplus1success)
        self.entropyFailure = self.__entropy(self.posteriorTplus1failure)      
        self.expectEntropy = np.multiply(self.entropySuccess, self.pSuccessGivenx) + np.multiply(self.entropyFailure, self.pFailureGivenx)
        self.minEntropyInd = np.argmin(self.expectEntropy)  # index of smallest expected entropy
        self.intensity = self.stimRange[self.minEntropyInd]  # stim intensity at minimum expected entropy

        self.iTrial += 1
        if self.iTrial == (self.nTrials -1):
            self.stop = 1
        logging.getLogger('EasyExp').info('computed intensity: {}'.format(self.intensity))

    def update(self, stair_id, direction, intensities=None, responses=None):
        """
        Updates stimulus intensity based on previous response.

        Parameters
        ----------
        :param stair_id: ID of current stair
        :type stair_id: int
        :param direction: direction of current staircase (0: up, 1:down)
        :type direction: int
        :param intensities: list of previously displayed intensities
        :type intensities: array-like
        :param responses: list of previous responses
        :type responses: array-like

        Returns
        -------
        :return intensity: new stimulus intensity
        :rtype intensity: float
        """
        self.cur_stair = stair_id

        # First, we make response and intensity lists from data
        if intensities is None:
            self._load_data()

        self._get_lists(intensity=intensities, response=responses)

        if self.cpt_stair <= self._options['warm_up']:
            # If warm-up phase, then present extremes values
            self.intensity = self._options['stimRange'][self.cpt_stair % 2]
            return self.intensity
        elif self.cpt_stair == self._options['warm_up'] + 1:
            # If this is the first trial for the current staircase, then returns initial intensity
            self.intensity = self._options['stimRange'][direction]
            return self.intensity

        init_time = time.time()
        self.addData(self.resp_list[0, self.cpt_stair-1])
        logging.getLogger('EasyExp').info('it took {} s'.format(time.time() - init_time))
        return self.intensity

    def addData(self, response):
        """
        Add the most recent response to start calculating the next stimulus intensity
        
        Arguments
        ---------
            Response:
                1: correct/right
                
                0: incorrect/left
        """
        self.response.append(response)
        
        self.intensity = None
        
        # Keep the posterior probability distribution that corresponds to the recorded response
        if response == 1:
            # select the posterior that corresponds to the stimulus intensity of lowest entropy
            self.pdf = self.posteriorTplus1success[Ellipsis, self.minEntropyInd]
        elif response == 0:
            self.pdf = self.posteriorTplus1failure[Ellipsis, self.minEntropyInd]

        # normalize the pdf
        self.pdf = self.pdf / np.sum(self.pdf)

        # Marginalized probabilities per parameter
        if self.gammaEQlambda:
            self.pThreshold = np.sum(self.pdf, axis=(1, 2))
            self.pSlope = np.sum(self.pdf, axis=(0, 2))
            self.pLapse = np.sum(self.pdf, axis=(0, 1))
            self.pGuess = self.pLapse
        else:
            self.pThreshold = np.sum(self.pdf, axis=(1, 2, 3))
            self.pSlope = np.sum(self.pdf, axis=(0, 2, 3))
            self.pLapse = np.sum(self.pdf, axis=(0, 1, 2))
            self.pGuess = np.sum(self.pdf, axis=(0, 1, 3))

        # Distribution means as expected values of parameters
        self.eThreshold = np.sum( np.multiply(self.threshold,   self.pThreshold))
        self.eSlope = np.sum( np.multiply(self.slope,       self.pSlope))
        self.eLapse = np.sum( np.multiply(self.lapseRate,   self.pLapse))
        self.eGuess = np.sum( np.multiply(self.guessRate,   self.pGuess))

        # Start calculating the next minimum entropy stimulus
        self.minEntropyStim()

    """
    From here start EasyExp-specific methods. Could be better to actually create an abstract class implementing these
    methods. However, then we may loose modularity if one wishes to use this class outside EasyExp.
    """

    @staticmethod
    def make_design(factors, options, conditions_name):
        """
        Generates trials list

        Parameters
        ----------
        nb_stairs
        :param factors: list of numbers of levels per factor
        :type factors: array-like
        :param options: Staircase options
        :type options: dict
        :param conditions_name: list of conditions (columns) name
        :type conditions_name: list

        Returns
        -------
        :return design: trials list (trials x conditions)
        :rtype design: ndarray
        :return conditions_name: updated list of conditions name
        :rtype conditions_name: list
        """
        factors.append(int(options['nbStairs']))

        factors = np.array(factors)  # Convert to numpy array
        cols = len(factors)  # Number of columns (factors)
        ssize = np.prod(factors)  # Total number of conditions
        ncycles = ssize
        design = np.zeros((ssize, cols + 1))
        for k in range(cols):
            settings = np.array(range(0, factors[k]))  # settings for kth factor
            nreps = ssize / ncycles  # repeats of consecutive values
            ncycles = ncycles / factors[k]  # repeats of sequence
            settings = np.tile(settings, (nreps, 1))  # repeat each value nreps times
            settings = np.reshape(settings, (1, settings.size), 'F')  # fold into a column
            settings = np.tile(settings, (1, ncycles))  # repeat sequence to fill the array
            design[:, k] = settings[:]

        nb_all_stairs = np.prod(factors)
        design[:, cols] = range(nb_all_stairs)  # Add methods' IDs

        design = np.tile(design, (options['nTrials'], 1))  # Make repetitions

        # Update list of conditions names
        conditions_name.append('staircaseDir')
        conditions_name.append('staircaseID')

        return design, conditions_name


