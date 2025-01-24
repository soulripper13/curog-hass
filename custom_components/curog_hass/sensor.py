import aiohttp
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
import pytz  # Make sure to install pytz if not already available

DOMAIN = "curog_hass"

# Set up logging
logger = logging.getLogger(__name__)

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
        """Return a unique ID for this entity."""
        return f"{self._registrator_id}_{self._name.replace(' ', '_').lower()}"

    @property
    def device_class(self):
        """Return the device class of the entity."""
        return "energy"

    @property
    def state_class(self):
        """Return the state class of the entity."""
        return "total_increasing"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._consumption = await fetch_energy_data(
            self._modem_id,
            self._api_key,
            self._registrator_id,
            self.name,
            self.hass.config.time_zone  # Pass the timezone from Home Assistant config
        )

async def fetch_energy_data(modem_id, api_key, registrator_id, consumption_type, timezone):
    """Fetch energy data from the API based on the type of consumption."""
    
    # Get current time in Home Assistant's timezone
    local_tz = pytz.timezone(timezone)
    local_time = datetime.now(local_tz)

    start_of_year = local_time.replace(month=1, day=1, hour=0, minute=0, second=0)
    start_timestamp = int(start_of_year.timestamp())
    end_timestamp = int(local_time.timestamp())

    url = f"https://lk.curog.ru/api.data/get_values/?modem_id={modem_id}&key={api_key}&from={start_timestamp}&to={end_timestamp}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                text = await response.text()  # Log the text response for debugging
                logger.error(f"Error fetching data: {text}")  # Log the error message
                return 0  # Handle API error appropriately
            
            try:
                data = await response.json()
            except aiohttp.ContentTypeError:
                text = await response.text()
                logger.error(f"Failed to decode JSON, received: {text}")
                return 0
            
            values = data["registrators"][registrator_id]["values"]

            current_date = local_time.strftime("%Y-%m-%d")
            current_month = local_time.strftime("%Y-%m")

            if consumption_type == "Daily Energy Consumption":
                filtered_data = [
                    item for item in values 
                    if datetime.utcfromtimestamp(item["timestamp"]).astimezone(local_tz).strftime("%Y-%m-%d") == current_date
                ]
            elif consumption_type == "Monthly Energy Consumption":
                filtered_data = [
                    item for item in values 
                    if datetime.utcfromtimestamp(item["timestamp"]).astimezone(local_tz).strftime("%Y-%m") == current_month
                ]
            else:
                return 0
            
            if len(filtered_data) > 1:
                return filtered_data[-1]["value"] - filtered_data[0]["value"]
    
    return 0

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities):
    """Set up sensor entities."""
    
    # Create instances for daily and monthly sensors only
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
    
    # Register the sensors in Home Assistant
    async_add_entities(sensors)
    
    return True

