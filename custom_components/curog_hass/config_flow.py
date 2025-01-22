from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol

class EnergyConsumptionConfigFlow(config_entries.ConfigFlow, domain="energy_consumption"):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Energy Consumption", data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._get_schema())

    def _get_schema(self):
        return vol.Schema({
            vol.Required("modem_id"): str,
            vol.Required("api_key"): str,
            vol.Required("registrator_id"): str,
        })
