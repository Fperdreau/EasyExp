from cli import *
from dialog import *

__version__ = '1.0.0'


class GuiWrapper(object):
    """
    Factory class returning instances of GUI
    """

    @staticmethod
    def factory(cli, data_type, inputs_data, **kwargs):
        """
        Factory
        :param cli: run in command line (True)
        :type cli: bool
        :param data_type: Type of data structure ('simple', 'nested')
        :type data_type: str
        :param inputs_data: Data structure loaded from json file
        :type inputs_data: dict
        :param kwargs: arguments passed to requested object's constructor. See SimpleCli, NestedCli, SimpleGui and
        NestedGui documentation for list of arguments.
        :rtype: BaseCli
        """
        try:
            if cli is True:
                if data_type == 'simple':
                    return SimpleCli(inputs_data, **kwargs)
                elif data_type == 'nested':
                    return NestedCli(inputs_data, **kwargs)
            else:
                if data_type == 'simple':
                    return SimpleGui(inputs_data, **kwargs)
                elif data_type == 'nested':
                    return NestedGui(inputs_data, **kwargs)
        except AttributeError as e:
            raise AttributeError('Make sure to provide arguments compatible with the type of GUI (CLI={}) '
                                 'and data format({}): {}'.format(cli, data_type, e))
        except TypeError as e:
            raise TypeError('Make sure to provide arguments compatible with the type of GUI (CLI={}) '
                            'and data format({}): {}'.format(cli, data_type, e))

if __name__ == '__main__':
    inputs = {
            "simple_input_int": 1,
            "simple_input_str": "some text",
            "bool_input": False,
            "select_input_str": ["option1", "option2", "option3"],
            "select_input_int": [0, 1, 2]
        }

    GuiWrapper.factory(False, 'nested', inputs)
