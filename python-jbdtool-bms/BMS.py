import serial
import struct
from datetime import datetime
from protection_states import ProtectionState

## Constants
basic_info_query = b'\xdd\xa5\x03\x00\xff\xfd\x77'
# Struct format onyl contains the static part. For every available NTC temp sensor, a 'H' will be added.
basic_info_boilerplate = ">HHHHHHIHcBBBB"
cell_voltages_query = b'\xdd\xa5\x04\x00\xff\xfc\x77'
# Same as above, just for the number of cells
cell_voltages_boilerplate = ">"


# Compares the checksum extracted from the response (third and second last bytes) and compares it with the caluclated checksum
def validate_response(data):
    length = data[3]
    received_checksum, = struct.unpack(">H", data[-3:-1])
    calculated_checksum = calculate_checksum(length, data[4:-3])
    return received_checksum == calculated_checksum


# Takes the actual data as list of bytes represented as integers and calculates the checksum
def calculate_checksum(length, data):
    return (sum(data) + length - 1) ^ 0xffff


def value_to_date(value):
    # unpack two bytes to date according to documentation
    return datetime(2000 + (value >> 9), (value >> 5) & 0x0f, value & 0x1f)


def value_to_protection_state(value):
    active_states = []
    # Iterate over all ProtectionStates and check if the specific bit is 1 (state active) or 0 (state inactive)
    for bit in range(16):
        if value & (1 << bit):
            active_states.append(ProtectionState(bit))
    return active_states


def value_to_balance_state(value, number_of_cells):
    balance_states = []
    for cell in range(number_of_cells):
        balance_states.append(bool(value & (1 << cell)))
    return balance_states


# Can be used if no BMS is connected. Supplies some data captured from my BMS
def debug_query(query):
    if query == basic_info_query:
        return b'\xdd\x03\x00\x1b\x05\x4c\x00\x00\x24\xf2\x2a\xf8\x00\x00\x28\xd2\x00\x00\x00\x00\x00\x00\x17\x56\x03\x04\x02\x09\x7f\x0b\xa9\xfa\xb0\x77'
    elif query == cell_voltages_query:
        return b'\xdd\x04\x00\x08\x0d\x42\x0d\x3c\x0d\x40\x0d\x3a\xfe\xcc\x77'
    else:
        raise ValueError("Invalid query")


def check_response(query, response):
    # The queried register address needs to match retuned register address and the third byte needs to be 0 for the query to be successful
    if query[2] != response[1] or response[2] != 0:
        raise ValueError("BMS sent error")

    if not validate_response(response):
        raise ValueError("Checksum mismatch")


class BMS:
    def __init__(self, serial_port, query_retries=3, offline=False):
        self.__debug = offline
        self.__query_reties = query_retries
        if not offline:
            self.connection = serial.Serial(port=serial_port, timeout=1, baudrate=9600, parity=serial.PARITY_EVEN,
                                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

        # Init variables
        self.number_of_cells = -1
        self.total_voltage = -1
        self.current = -1
        self.residual_capacity = -1
        self.nominal_capacity = -1
        self.cycle_times = -1
        self.manufacturing_date = datetime.now()
        self.rsoc = -1
        self.balance_states = []
        self.active_protection_states = []
        self.software_version = b''
        self.discharge_status = False
        self.charge_status = False
        self.cell_voltages = []
        self.temperatures = []

        # Initialize data
        self.__basic_info_struct_format, self.__cell_voltages_struct_format = self.__init_bms()
        self.query_all()

    def __init_bms(self):
        # Only doing this once as these values will not change, saves some µA :D
        response = self.__query_bms(basic_info_query)
        check_response(basic_info_query, response)
        # Read number of NTC temp sensors from byte 26 to adjust format
        number_of_ntcs = response[26]
        # Read number of cells from byte 25 to adjust format
        self.number_of_cells = response[25]
        # Append unsigned shorts to boilerplates to decode BMS messages later...
        return basic_info_boilerplate + number_of_ntcs * "H", cell_voltages_boilerplate + self.number_of_cells * "H"

    def __query_bms(self, query):
        if self.__debug:
            return debug_query(query)
        response = bytearray()
        retries = 0

        # Read first 4 bytes (stat byte, register address, check byte and message length)
        while len(response) < 4:
            self.connection.write(query)
            response.extend(self.connection.read(4))
            retries += 1
            if retries > self.__query_reties:
                raise ValueError("Cloud not get a response from BMS. Maybe not connected properly?")

        # Length of the response is given in byte 3, determines how much bytes to read (+3 for 2 checksum bytes and stop byte)
        length = response[3]
        response.extend(self.connection.read(length + 3))
        return response

    def query_all(self):
        self.query_basic_info()
        self.query_cell_voltages()

    def query_basic_info(self):
        response = self.__query_bms(basic_info_query)
        check_response(basic_info_query, response)
        unpacked = struct.unpack(self.__basic_info_struct_format, response[4:-3])
        self.total_voltage = unpacked[0] / 100  # total voltage in 10mV
        self.current = unpacked[1] / 100  # current in 10mA
        self.residual_capacity = unpacked[2] / 100  # residual capacity in 10mAh
        self.nominal_capacity = unpacked[3] / 100  # nominal capacity in 10mAh
        self.cycle_times = unpacked[4]  # cycle times
        self.manufacturing_date = value_to_date(unpacked[5])  # manufacturing date
        self.balance_states = value_to_balance_state(unpacked[6], self.number_of_cells)
        self.active_protection_states = value_to_protection_state(unpacked[7])  # Protection state
        self.software_version = unpacked[8]  # 8 Software version
        self.rsoc = unpacked[9]  # remaining state of charge in percent
        self.discharge_status = bool(int(bin(unpacked[10])[2]))  # discharging status
        self.charge_status = bool(int(bin(unpacked[10])[3]))  # charging status
        self.temperatures = [(raw - 2731) / 10 for raw in unpacked[13:]]  # Temp in 100mK converted to °C

    def query_cell_voltages(self):
        response = self.__query_bms(cell_voltages_query)
        check_response(cell_voltages_query, response)
        raw_voltages = struct.unpack(self.__cell_voltages_struct_format, response[4:-3])
        # Unit is mV, divide by 1000 to get volts
        self.cell_voltages = [raw / 1000 for raw in raw_voltages]


if __name__ == "__main__":
    for i in range(10000):
        BMS('', offline=True)
