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
        return "total_increasing"

    async def async_update(self):
        self._consumption = await fetch_energy_data(
            self._modem_id,
            self._api_key,
            self._registrator_id,
            self.name
        )

async def fetch_energy_data(modem_id, api_key, registrator_id, consumption_type):
    """Fetch energy data using SERVER TIME (not Vladivostok)."""
    # Get current time in the server's timezone
    server_time = dt_util.now()  # Use Home Assistant's timezone-aware now()
    
    # Calculate start of the year in SERVER TIME
    start_of_year = server_time.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    start_timestamp = int(start_of_year.timestamp())
    end_timestamp = int(server_time.timestamp())

    url = f"https://lk.curog.ru/api.data/get_values/?modem_id={modem_id}&key={api_key}&from={start_timestamp}&to={end_timestamp}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return 0
            
            data = await response.json()
            values = data["registrators"][registrator_id]["values"]

            # Use server time for filtering
            current_date = server_time.strftime("%Y-%m-%d")
            current_month = server_time.strftime("%Y-%m")

            filtered_data = []
            for item in values:
                # Convert API timestamp to SERVER TIME
                item_time = dt_util.utc_from_timestamp(item["timestamp"])  # Convert to UTC datetime
                item_local_time = dt_util.as_local(item_time)  # Convert to server's timezone

                if consumption_type == "Daily Energy Consumption":
                    if item_local_time.strftime("%Y-%m-%d") == current_date:
                        filtered_data.append(item)
                elif consumption_type == "Monthly Energy Consumption":
                    if item_local_time.strftime("%Y-%m") == current_month:
                        filtered_data.append(item)

            if len(filtered_data) > 1:
                return filtered_data[-1]["value"] - filtered_data[0]["value"]
    
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
                                 entry.data["registrator_id"])
    ]
    async_add_entities(sensors)
    return True
