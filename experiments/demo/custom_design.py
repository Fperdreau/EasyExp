# This file is part of Snaky_experiment

from random import shuffle

__author__ = "Florian Perdreau"
__email__ = "fp@florianperdreau.fr"
__copyright = "Florian Perdreau, 2016"


def custom_design(design):
    """
    This function generates a customized randomization of a trials list with the constraint that self-motion direction
    should be alternated across trials
    Example:
        Trial 1 to the left
        Trial 2 to the right

    :param design: trials list. This is a list of dictionaries with one dictionary per trial
    :type design: list

    :return:
    """
    # First, we randomize the whole list of trials
    shuffle(design)

    leftlist = [design[ii] for ii in range(len(design)) if design[ii]['side'] == 'left']
    rightlist = [design[ii] for ii in range(len(design)) if design[ii]['side'] == 'right']
    new_design = [j for i in zip(leftlist, rightlist) for j in i]

    return new_design
