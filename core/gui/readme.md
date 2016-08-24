# DialogGUI
Version: 1.1

Florian Perdreau (f.perdreau@donders.ru.nl)

# Description
This class renders a GUI form from data provided by a JSON settings file. It handles methods to read and parse the
settings file, as well as inputs given by the user, and update the settings file accordingly.
The JSON file should be formatted as follow:
```
    {
        "section_name": {
            "input_name": {
                "label": "input_label",
                "type": "input_type",
                "value": input_value,
                "options": list_of_possible_inputs
            }
        }
    }

    example:
    {
        "Display": {
            "distance": {
                "label": "Distance",
                "type": "text",
                "value": 1470.0
            },
            "fullscreen": {
                "label": "Full screen",
                "type": "checkbox",
                "options": [true, false],
                "value": false
            }
        }
    }

```
Input type can be: 'text', 'checkbox' or 'select'

@usage:
```
    # Path to settings file
    path_to_settings_file = "settings.json"

    # Read data from settings file
    with open(path_to_settings_file) as data_file:
        data = json.load(data_file)

    # Render GUI form
    info = DialogGUI(data)

    # Update settings file with inputs provided by the user (inputs are stored in info.out)
    with open(path_to_settings_file, 'w', 0) as fid:
        json.dump(info.out, fid, indent=4)
```