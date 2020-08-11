from enum import Enum


# The protection state of the BMS is given as two bytes, 16 bits. The vlaue of the Enum corresponds to it's position
# in the bit range.
class ProtectionState(Enum):
    SINGLE_OVERVOLTAGE = 0
    SINGLE_UNDERVOLTAGE = 1
    PACK_OVERVOLTAGE = 2
    PACK_UNDERVOLTAGE = 3
    CHARGE_OVER_TEMPERATURE = 4
    CHARGE_UNDER_TEMPERATURE = 5
    DISCHARGE_OVER_TEMPERATURE = 6
    DISCHARGE_UNDER_TEMPERATURE = 7
    CHARGE_OVER_CURRENT = 8
    DISCHARGE_OVER_CURRENT = 9
    SHORT_CIRCUIT = 10
    FRONT_DETECTION_IC_ERROR = 11
    MOS_SOFTWARE_LOCK = 12
