from os.path import dirname, abspath
import sys
import numpy as np

# Environmental settings
root_folder = dirname(dirname(abspath('__dir__')))
sys.path.append("{}/libs".format(root_folder))

from core.Devices import Devices
import logging
logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    folder = "{}/experiments/demo/".format(root_folder)
    device = Devices(exp_folder=folder, base_name='test')
    device.init()
