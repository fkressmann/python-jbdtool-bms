import serial
import struct
from datetime import datetime

## Constants
basic_info_query = b'\xdd\xa5\x03\x00\xff\xfd\x77'
# Struct format onyl contains the static part. For every available NTC temp sensor, a 'H' will be added.
basic_info_boilerplate = ">HHHHHHHHHBBBBB"
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
    data_sum = sum(data)
    return (data_sum + length - 1) ^ 0xffff


def value_to_date(value):
    # unpack two bytes to date according to documentation
    return datetime(2000 + (value >> 9), (value >> 5) & 0x0f, value & 0x1f)


# Can be set if no BMS is connected
def debug_query(query):
    if query == basic_info_query:
        return b'\xdd\x03\x00\x1b\x05\x4c\x00\x00\x24\xf2\x2a\xf8\x00\x00\x28\xd2\x00\x00\x00\x00\x00\x00\x17\x56\x03\x04\x02\x09\x7f\x0b\xa9\xfa\xb0\x77'
    elif query == cell_voltages_query:
        return b'\xdd\x04\x00\x08\x0d\x42\x0d\x3c\x0d\x40\x0d\x3a\xfe\xcc\x77'
    else:
        return b''


def check_response(query, response):
    # The queried register address needs to match retuned register address and the third byte needs to be 0 for the query to be successful
    if query[2] != response[1] or response[2] != 0:
        raise ValueError("Response has error")

    if not validate_response(response):
        raise ValueError("Checksum mismatch")


class BMS:
    def __init__(self, serial_port, query_retries=3, offline=False):
        self.debug = offline
        self.query_reties = query_retries
        if not offline:
            self.connection = serial.Serial(port=serial_port, timeout=1, baudrate=9600, parity=serial.PARITY_EVEN,
                                            stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

        self.basic_info_struct_format, self.cell_voltages_struct_format = self.__init_bms()

        # ToDo: Move to method
        self.voltage, self.current, self.residual_capacity, self.nominal_capacity, self.cycle_times, self.date,\
            self.rsoc, self.discharge_status, self.charge_status= self.get_basic_info()
        self.cell_voltages = self.get_cell_voltages()

    def __init_bms(self):
        # Only doing this once as these values will not change, saves some µA :D
        response = self.__query_bms(basic_info_query)
        check_response(basic_info_query, response)
        # Read number of NTC temp sensors from byte 26 to adjust format
        number_of_ntcs = response[26]
        # Read number of cells from byte 25 to adjust format
        number_of_cells = response[25]
        # Append unsigned shorts to boilerplates to decode BMS messages later...
        return basic_info_boilerplate + number_of_ntcs * "H", cell_voltages_boilerplate + number_of_cells * "H"

    def __query_bms(self, query):
        if self.debug:
            return debug_query(query)
        response = bytearray()
        retries = 0

        # Read first 4 bytes (stat byte, register address, check byte and message length)
        while len(response) < 4:
            self.connection.write(query)
            response.extend(self.connection.read(4))
            retries += 1
            if retries > self.query_reties:
                raise ValueError("Cloud not get a response from BMS. Maybe not connected properly?")

        # Length of the response is given in byte 3, determines how much bytes to read (+3 for 2 checksum bytes and stop byte)
        length = response[3]
        response.extend(self.connection.read(length + 3))

        return response

    def get_basic_info(self):
        response = self.__query_bms(basic_info_query)
        check_response(basic_info_query, response)
        unpacked = struct.unpack(self.basic_info_struct_format, response[4:-3])
        data = (
            unpacked[0] / 100,  # total voltage in 10mV
            unpacked[1] / 100,  # current in 10mA
            unpacked[2] / 100,  # residual capacity in 10mAh
            unpacked[3] / 100,  # nominal capacity in 10mAh
            unpacked[4],  # cycle times
            value_to_date(unpacked[5]),  # manufacturing date
            # 6 balance state low
            # 7 valance state hight
            # 8 Protection state
            # 9 Software version
            unpacked[10], # remaining state of charge in percent
            bool(int(bin(unpacked[11])[2])), # discharging status
            bool(int(bin(unpacked[11])[3])), # charging status
        )
        return data

    def get_cell_voltages(self):
        response = self.__query_bms(cell_voltages_query)
        check_response(cell_voltages_query, response)
        return struct.unpack(self.cell_voltages_struct_format, response[4:-3])
