import aiohttp
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.util import dt as dt_util  # Import Home Assistant's time utilities

DOMAIN = "curog_hass"

class EnergyConsumptionSensor(SensorEntity):
    """Representation of an energy consumption sensor."""

    def __init__(self, name, consumption, modem_id, api_key, registrator_id):
        self._name = name
        self._consumption = consumption
        self._modem_id = modem_id
        self._api_key = api_key
        self._registrator_id = registrator_id
        self._hour_start_daily_value = None  # Daily sensor value at start of current hour
        self._current_hour = None  # Track the current hour for reset
        self._last_reset_day = None  # Track the day of the last reset
        self._is_initial_setup = True  # Flag for initial historical data fetch

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._consumption

    @property
    def unit_of_measurement(self):
        return "kWh"

    @property
    def unique_id(self):
        return f"{self._registrator_id}_{self._name.replace(' ', '_').lower()}"

    @property
    def device_class(self):
        return "energy"

    @property
    def state_class(self):
        return "measurement"  # Changed to measurement for per-hour values

    async def async_update(self):
        """Update the sensor's state."""
        server_time = dt_util.now()
        current_day = server_time.strftime("%Y-%m-%d")
        current_hour = server_time.strftime("%Y-%m-%d %H")

        if self._name == "Hourly Energy Consumption":
            # Check if the hour has changed to reset the sensor
            if self._current_hour != current_hour:
                self._consumption = 0
                self._hour_start_daily_value = None
                self._current_hour = current_hour

            # Check if the day has changed to reset tracking variables
            if self._last_reset_day != current_day:
                self._last_reset_day = current_day
                self._is_initial_setup = False

            # Get the current daily sensor's value
            daily_sensor = next(
                (s for s in self.hass.data[DOMAIN]["sensors"] if s.name == "Daily Energy Consumption"),
                None
            )
            if daily_sensor:
                current_daily_value = daily_sensor.state
                if current_daily_value is not None:
                    if self._hour_start_daily_value is None:
                        # Initialize with the current daily value at the start of the hour
                        self._hour_start_daily_value = current_daily_value
                    else:
                        # Calculate hourly consumption as the difference in daily values
                        delta = current_daily_value - self._hour_start_daily_value
                        if delta >= 0:  # Ensure no negative values
                            self._consumption = delta
        else:
            # Update daily and monthly sensors using API data
            self._consumption = await fetch_energy_data(
                self._modem_id,
                self._api_key,
                self._registrator_id,
                self.name
            )

async def fetch_energy_data(modem_id, api_key, registrator_id, consumption_type, start_time=None, end_time=None):
    """Fetch energy data using SERVER TIME (not Vladivostok)."""
    server_time = dt_util.now() if end_time is None else end_time
    if start_time is None:
        # Default: start of the year for daily/monthly
        start_of_year = server_time.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        start_timestamp = int(start_of_year.timestamp())
    else:
        start_timestamp = int(start_time.timestamp())
    end_timestamp = int(server_time.timestamp())

    url = f"https://lk.curog.ru/api.data/get_values/?modem_id={modem_id}&key={api_key}&from={start_timestamp}&to={end_timestamp}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return 0
            
            data = await response.json()
            values = data["registrators"][registrator_id]["values"]

            if consumption_type in ["Daily Energy Consumption", "Monthly Energy Consumption"]:
                # Use server time for filtering
                current_date = server_time.strftime("%Y-%m-%d")
                current_month = server_time.strftime("%Y-%m")

                filtered_data = []
                for item in values:
                    item_time = dt_util.utc_from_timestamp(item["timestamp"])
                    item_local_time = dt_util.as_local(item_time)

                    if consumption_type == "Daily Energy Consumption":
                        if item_local_time.strftime("%Y-%m-%d") == current_date:
                            filtered_data.append(item)
                    elif consumption_type == "Monthly Energy Consumption":
                        if item_local_time.strftime("%Y-%m") == current_month:
                            filtered_data.append(item)

                if len(filtered_data) > 1:
                    return filtered_data[-1]["value"] - filtered_data[0]["value"]
            else:
                # Return raw values for historical hourly processing
                return values
    
    return 0

async def fetch_historical_hourly_data(modem_id, api_key, registrator_id, current_hour):
    """Fetch and process data for the past 12 hours to initialize hourly sensor."""
    server_time = dt_util.now()
    start_time = server_time - timedelta(hours=12)
    values = await fetch_energy_data(modem_id, api_key, registrator_id, "historical", start_time, server_time)
    
    if not values:
        return 0

    # Group values by hour
    hourly_values = {}
    for item in values:
        item_time = dt_util.utc_from_timestamp(item["timestamp"])
        item_local_time = dt_util.as_local(item_time)
        hour_key = item_local_time.strftime("%Y-%m-%d %H")
        if hour_key not in hourly_values:
            hourly_values[hour_key] = []
        hourly_values[hour_key].append(item)

    # Try to get data for the current hour first
    if current_hour in hourly_values:
        data = hourly_values[current_hour]
        if len(data) > 1:
            return data[-1]["value"] - data[0]["value"]

    # Fallback to the most recent hour with data
    for hour in sorted(hourly_values.keys(), reverse=True):
        data = hourly_values[hour]
        if len(data) > 1:
            return data[-1]["value"] - data[0]["value"]
    
    return 0

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities):
    sensors = [
        EnergyConsumptionSensor("Daily Energy Consumption", 0,
                                entry.data["modem_id"],
                                entry.data["api_key"],
                                entry.data["registrator_id"]),
        EnergyConsumptionSensor("Monthly Energy Consumption", 0,
                                entry.data["modem_id"],
                                entry.data["api_key"],
                                entry.data["registrator_id"]),
        EnergyConsumptionSensor("Hourly Energy Consumption", 0,
                                entry.data["modem_id"],
                                entry.data["api_key"],
                                entry.data["registrator_id"])
    ]
    # Store sensors in hass.data for access by hourly sensor
    hass.data[DOMAIN]["sensors"] = sensors

    # Initialize hourly sensor with historical data
    current_hour = dt_util.now().strftime("%Y-%m-%d %H")
    for sensor in sensors:
        if sensor.name == "Hourly Energy Consumption":
            sensor._consumption = await fetch_historical_hourly_data(
                entry.data["modem_id"],
                entry.data["api_key"],
                entry.data["registrator_id"],
                current_hour
            )
            sensor._current_hour = current_hour
            sensor._last_reset_day = dt_util.now().strftime("%Y-%m-%d")
            break

    async_add_entities(sensors)
    return True
