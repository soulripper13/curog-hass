# curog-hass
Home assistant integration for energy monitoring from lk.curog.ru using its API
# Energy Consumption Integration for Home Assistant

This custom integration for Home Assistant allows you to monitor energy consumption from a specific modem using an API. It provides two sensor entities: hourly, daily, and monthly energy consumption. The monthly sensor resets automatically at the beginning of each month.

## Features

- Fetches energy consumption data from an external API.
- Provides three types of sensors:
  - **Daily Energy Consumption**
  - **Monthly Energy Consumption** (resets automatically at the start of each month)
- Allows configuration through the Home Assistant UI.
- Uses asynchronous calls for efficient data fetching.

## Requirements

- Home Assistant (version 2023.12 or later)
- Python 3.8 or later
- `aiohttp` library (included in the integration)

## Installation

1. **Download the Integration**
   - Clone this repository or download it as a ZIP file.

2. **Copy to Custom Components Directory**
- Copy the `energy_consumption` directory to your Home Assistant `custom_components` directory.


3. **Restart Home Assistant**
- Restart your Home Assistant instance to load the new integration.

## Configuration

1. **Add the Integration**
- Go to **Configuration** > **Integrations** in the Home Assistant UI.
- Click on **Add Integration** and search for "Energy Consumption".
- Enter the required configuration parameters:
  - **Modem ID**: Your modem's unique identifier.
  - **API Key**: Your API key for accessing the data.
  - **Registrator ID**: The ID of the registrator you want to monitor.
  - You can find the necessary parameters on lk.curog.ru
    


2. **Entities Created**
- After successful configuration, three sensor entities will be created:
  - `sensor.daily_energy_consumption`
  - `sensor.monthly_energy_consumption`

## Usage

- The sensors will automatically fetch data from the specified API and update their values based on the latest readings.
- The monthly sensor will reset its value at the beginning of each month, allowing you to track monthly energy usage effectively.

## Troubleshooting

- If you encounter issues with fetching data, check the logs in Home Assistant for any error messages related to this integration.
- Ensure that your API endpoint is accessible and that you have provided valid credentials.

## Contributing

Contributions are welcome! If you find bugs or want to add features, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author Information

Created by [Soulripper13](https://github.com/soulripper13).



