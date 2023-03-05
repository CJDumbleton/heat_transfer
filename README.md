# Heat Transfer

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)
<!--
[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]
<!---->

This is a heat transfer coefficient sensor for Home Assistant calculated from the [rate of heat loss divided by temperature difference](https://en.wikipedia.org/wiki/Newton's_law_of_cooling#Simplified_formulation). You can create one sensor for your whole home or sensors for each room with an outside wall where you have a temperature sensor.

The heat transfer coefficient is a measure of how well insulated your room / house is.

Use the sensor to assess the impact of new insulation interventions eg keeping the window closed at night, hanging insulating curtains or blinds, loft insulation, cavity wall insulation etc.

The sensor will only operate:
- between midnight and 4am (It is assumed any heating and air conditioning is off during this period.);
- when the wind speed is under 10 km/h; and
- when precipitation probability is under 20%.

**This integration will set up the following sensor:**

*Heat Transfer Coefficient* ```heat_transfer_coefficient```
- The rate of heat loss divided by the temperature difference

UNDER DEVELOPMENT. WAIT FOR FIRST RELEASE BEFORE DOWNLOADING

<!--

## Installation

### HACS
TBD

### Manual
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `custom_components/heat_transfer`.
1. Download _all_ the files from the `custom_components/heat_transfer/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Settings" -> "Devices & Services" -> "Integrations" click "+" and search for "Heat Transfer"

## Usage
To use Heat Transfer, check the documentation for your preferred way to set up the sensor:
- [UI/Frontend (Config Flow)](https://github.com/CJDumbleton/heat_transfer/Documentation/config_flow)
- [YAML]()

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits
With thanks to the following repos on which the code is largely based:
- [<img src="https://github.com/ludeeus.png" style="margin: 0.2em; vertical-align: middle; border-radius: 50%;border: solid 0.1px grey;" width="24"/> @ludeeus](https://github.com/ludeeus) [Integration Blueprint](https://github.com/ludeeus/integration_blueprint)
- [<img src="https://github.com/dolezsa.png" style="margin: 0.2em; vertical-align: middle; border-radius: 50%;border: solid 0.1px grey;" width="24"/> @dolezsa](https://github.com/dolezsa) [Thermal Comfort](https://github.com/dolezsa/thermal_comfort)

***

[heat_transfer]: https://github.com/CJDumbleton/heat_transfer
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/ludeeus/integration_blueprint.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-CJ%20Dumbleton%20%40cjdumbleton-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/CJDumbleton/heat_transfer.svg?style=for-the-badge
[releases]: https://github.com/CJDumbleton/heat_transfer/releases
