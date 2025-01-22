from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "energy_consumption"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Energy Consumption component."""
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry):
    """Set up a config entry for Energy Consumption."""
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setup(entry, "sensor")
    
    return True
