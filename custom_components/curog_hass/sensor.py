import aiohttp
import logging
from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
import pytz

DOMAIN = "curog_hass"
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
            self.name,
            self.hass.config.time_zone
        )

async def fetch_energy_data(modem_id, api_key, registrator_id, consumption_type, timezone):
    # Your existing fetch logic here...

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities):
    """Set up sensor entities from a config entry."""
    
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
    
    logger.debug("Curog Hass sensors set up successfully.")
    
    return True
