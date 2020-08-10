# python-jbdtool-bms
This Python library allows connection to Lithium BMS with a UART to USB adapter and read the battery information.

The information on how the protocol works was taken from a more or less official excel file I found online (included in the resources folder)

It's currently under development and may still deliver incorrect data.

## Documentation
### Initialisation
```bms = BMS("/path/to/serial")```
an optional debug=True parameter can be included to load some sample data instead of reading fromt he serial port. In this case, the first Parameter will be ignored.

### Methods
```query_basic_info()``` queries everything but single cell voltages (as it's one call to the BMS)

```query_cell_voltages()``` queries onlt the single cell voltages (one call, too)

```query_all()``` queries both of the above

### Parameters
The readings can be accessed directly on the instance:
- ```active_protection_states``` protection modes currently active (enum list)
- ```balance_state``` Whether a single cell is currently balanced (bool list)
- ```cell_voltages``` Single cell voltages in volts (V) (float list)
- ```current``` Current flowing. Negative for discharge, positive for charging (float)
- ```cycle_times``` (int)
- ```discharge_status``` (bool)
- ```manufacturing_date``` (datetime)
- ```nominal_capacity``` in ampere hours (Ah) (float)
- ```number_of_cells``` (int)
- ```residual_capacity``` in ampere hours (Ah) (float)
- ```rsoc``` remaining state of charge in percent (int)
- ```software_version``` (bytearray / not sure how to interpret this...)
- ```temperatures``` of all connected sensors, mostly BMS internal and external cell probe (float list)
- ```toal_voltage``` in volts (V)

## ToDo / Known Issues
- Balance state is the wrong way around, first cell is last value in list at the moment
- Only parse data which does not change once (like manufacturing date)
- Include energy saver mode to only query important data (my system is driven by that battery, so every µA counts :D)
