"""Support for Sunpower sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

from homeassistant.const import (
    TIME_SECONDS,
    DATA_KILOBYTES,
    FREQUENCY_HERTZ,
    ENERGY_KILO_WATT_HOUR,
    POWER_KILO_WATT,
    POWER_VOLT_AMPERE,
    PERCENTAGE,
    ELECTRIC_POTENTIAL_VOLT,
    ELECTRIC_CURRENT_AMPERE,
    TEMP_CELSIUS,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_VOLTAGE,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_POWER_FACTOR
)

from homeassistant.components.sensor import (
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL,
    STATE_CLASS_TOTAL_INCREASING
)

from .const import (
    DOMAIN,
    SUNPOWER_COORDINATOR,
    SUNPOWER_DESCRIPTIVE_NAMES,
    PVS_DEVICE_TYPE,
    INVERTER_DEVICE_TYPE,
    METER_DEVICE_TYPE,
    PVS_SENSORS,
    METER_SENSORS,
    INVERTER_SENSORS,
)
from .entity import SunPowerPVSEntity, SunPowerMeterEntity, SunPowerInverterEntity


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Sunpower sensors."""
    sunpower_state = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug("Sunpower_state: %s", sunpower_state)

    if not SUNPOWER_DESCRIPTIVE_NAMES in config_entry.data:
        config_entry.data[SUNPOWER_DESCRIPTIVE_NAMES] = False
    do_descriptive_names = config_entry.data[SUNPOWER_DESCRIPTIVE_NAMES]

    coordinator = sunpower_state[SUNPOWER_COORDINATOR]
    sunpower_data = coordinator.data

    if PVS_DEVICE_TYPE not in sunpower_data:
        _LOGGER.error("Cannot find PVS Entry")
    else:
        pvs = next(iter(sunpower_data[PVS_DEVICE_TYPE].values()))

        entities = []
        for sensor in PVS_SENSORS:
            if do_descriptive_names:
                title = f"{pvs['DEVICE_TYPE']} {PVS_SENSORS[sensor][1]}"
            else:
                title = PVS_SENSORS[sensor][1]
            spb = SunPowerPVSBasic(
                coordinator,
                pvs,
                PVS_SENSORS[sensor][0],
                title,
                PVS_SENSORS[sensor][2],
                PVS_SENSORS[sensor][3],
                PVS_SENSORS[sensor][4],
                PVS_SENSORS[sensor][5],
            )
            if spb.native_value is not None: # ensure we can pull a value here, otherwise throw out this value
                entities.append(spb)

        if METER_DEVICE_TYPE not in sunpower_data:
            _LOGGER.error("Cannot find any power meters")
        else:
            for data in sunpower_data[METER_DEVICE_TYPE].values():
                for sensor in METER_SENSORS:
                    if do_descriptive_names:
                        title = f"{data['DESCR']} {METER_SENSORS[sensor][1]}"
                    else:
                        title = METER_SENSORS[sensor][1]
                    smb = SunPowerMeterBasic(
                        coordinator,
                        data,
                        pvs,
                        METER_SENSORS[sensor][0],
                        title,
                        METER_SENSORS[sensor][2],
                        METER_SENSORS[sensor][3],
                        METER_SENSORS[sensor][4],
                        METER_SENSORS[sensor][5],
                    )
                    if smb.native_value is not None: # ensure we can pull a value here, otherwise throw out this value
                        entities.append(smb)

        if INVERTER_DEVICE_TYPE not in sunpower_data:
            _LOGGER.error("Cannot find any power inverters")
        else:
            for data in sunpower_data[INVERTER_DEVICE_TYPE].values():
                for sensor in INVERTER_SENSORS:
                    if do_descriptive_names:
                        title = f"{data['DESCR']} {INVERTER_SENSORS[sensor][1]}"
                    else:
                        title = INVERTER_SENSORS[sensor][1]
                    sib = SunPowerInverterBasic(
                        coordinator,
                        data,
                        pvs,
                        INVERTER_SENSORS[sensor][0],
                        title,
                        INVERTER_SENSORS[sensor][2],
                        INVERTER_SENSORS[sensor][3],
                        INVERTER_SENSORS[sensor][4],
                        INVERTER_SENSORS[sensor][5]
                    )
                    if sib.native_value is not None: # ensure we can pull a value here, otherwise throw out this value
                        entities.append(sib)

    # Custom calculations for to-grid and to-home.
    meterToGrid = SunPowerMeterCalculatedToGrid(
        coordinator
        )

    entities.append(meterToGrid)

    meterFromGrid = SunPowerMeterCalculatedFromGrid(
        coordinator
        )

    entities.append(meterFromGrid)

    async_add_entities(entities, True)


class SunPowerPVSBasic(SunPowerPVSEntity, SensorEntity):
    """Representation of SunPower PVS Stat"""

    def __init__(self, coordinator, pvs_info, field, title, unit, icon, device_class, state_class):
        """Initialize the sensor."""
        super().__init__(coordinator, pvs_info)
        self._title = title
        self._field = field
        self._unit = unit
        self._icon = icon
        self._my_device_class = device_class
        self._my_state_class = state_class

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return device class."""
        return self._my_device_class

    @property
    def state_class(self):
        """Return state class."""
        return self._my_state_class

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def name(self):
        """Device Name."""
        return self._title

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return f"{self.base_unique_id}_pvs_{self._field}"

    @property
    def native_value(self):
        """Get the current value"""
        return self.coordinator.data[PVS_DEVICE_TYPE][self.base_unique_id].get(self._field, None)


class SunPowerMeterBasic(SunPowerMeterEntity, SensorEntity):
    """Representation of SunPower Meter Stat"""

    def __init__(self, coordinator, meter_info, pvs_info, field, title, unit, icon,
                 device_class, state_class):
        """Initialize the sensor."""
        super().__init__(coordinator, meter_info, pvs_info)
        self._title = title
        self._field = field
        self._unit = unit
        self._icon = icon
        self._my_device_class = device_class
        self._my_state_class = state_class

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return device class."""
        return self._my_device_class

    @property
    def state_class(self):
        """Return state class."""
        return self._my_state_class

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def name(self):
        """Device Name."""
        return self._title

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return f"{self.base_unique_id}_pvs_{self._field}"

    @property
    def native_value(self):
        """Get the current value"""
        return self.coordinator.data[METER_DEVICE_TYPE][self.base_unique_id].get(self._field, None)


class SunPowerMeterCalculatedFromGrid(CoordinatorEntity, SensorEntity):
    """Representation of SunPower Meter Stat"""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self):

        # We want to retrieve two values: the current consumption and the current production.
        meterData = self.coordinator.data[METER_DEVICE_TYPE]

        # There are two: consumption and production. Production always comes first.
        meterAsList = list(meterData)
        productionDataValues = meterAsList[0]
        consumptionDataValues = meterAsList[1]
            
        consumptionData = float(meterData[consumptionDataValues]['p_3phsum_kw'])
        productionData = float(meterData[productionDataValues]['p_3phsum_kw'])

        _LOGGER.debug("CalculatedFromGrid: consumption: %f  production %f  diff: %f", consumptionData, productionData, consumptionData - productionData)

        if(productionData > consumptionData):
            return 0.0
        
        return consumptionData - productionData

    @property
    def device_info(self):
        """Sunpower Meter device info."""
        device_info = {
            "identifiers": {(DOMAIN, "CalculatedFromGrid")},
            "name": "CalculatedFromGrid",
            "manufacturer": "SunPower",
            "model": "PVS6",
        }

        return device_info

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return POWER_KILO_WATT

    @property
    def device_class(self):
        """Return device class."""
        return DEVICE_CLASS_POWER

    @property
    def state_class(self):
        """Return state class."""
        return STATE_CLASS_MEASUREMENT

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:flash"

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return "GridConsumptionCalculated"

    @property
    def name(self):
        """Device Name."""
        return "Consumption From Grid"

class SunPowerMeterCalculatedToGrid(CoordinatorEntity, SensorEntity):
    """Representation of SunPower Meter Stat"""

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self):

        # We want to retrieve two values: the current consumption and the current production.
        meterData = self.coordinator.data[METER_DEVICE_TYPE]

        # There are two: consumption and production. Production always comes first.
        meterAsList = list(meterData)
        productionDataValues = meterAsList[0]
        consumptionDataValues = meterAsList[1]
            
        consumptionData = float(meterData[consumptionDataValues]['p_3phsum_kw'])
        productionData = float(meterData[productionDataValues]['p_3phsum_kw'])

        _LOGGER.debug("CalculatedToGrid: consumption: %f  production %f  diff: %f", consumptionData, productionData, consumptionData - productionData)

        if(productionData > consumptionData):
            return productionData - consumptionData;
        
        return 0.0

    @property
    def device_info(self):
        """Sunpower Meter device info."""
        device_info = {
            "identifiers": {(DOMAIN, "CalculatedToGrid")},
            "name": "CalculatedToGrid",
            "manufacturer": "SunPower",
            "model": "PVS6",
        }

        return device_info

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return POWER_KILO_WATT

    @property
    def device_class(self):
        """Return device class."""
        return DEVICE_CLASS_POWER

    @property
    def state_class(self):
        """Return state class."""
        return STATE_CLASS_MEASUREMENT

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return "mdi:flash"

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return "GridProductionCalculated"

    @property
    def name(self):
        """Device Name."""
        return "Production To Grid"

class SunPowerInverterBasic(SunPowerInverterEntity, SensorEntity):
    """Representation of SunPower Meter Stat"""

    def __init__(self, coordinator, inverter_info, pvs_info, field, title, unit, icon,
                 device_class, state_class):
        """Initialize the sensor."""
        super().__init__(coordinator, inverter_info, pvs_info)
        self._title = title
        self._field = field
        self._unit = unit
        self._icon = icon
        self._my_device_class = device_class
        self._my_state_class = state_class

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_class(self):
        """Return device class."""
        return self._my_device_class

    @property
    def state_class(self):
        """Return state class."""
        return self._my_state_class

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def name(self):
        """Device Name."""
        return self._title

    @property
    def unique_id(self):
        """Device Uniqueid."""
        return f"{self.base_unique_id}_pvs_{self._field}"

    @property
    def native_value(self):
        """Get the current value"""
        return self.coordinator.data[INVERTER_DEVICE_TYPE][self.base_unique_id].get(self._field, None)
