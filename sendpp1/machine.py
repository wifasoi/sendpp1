'''
┌──────┬───────────────────────────┬───────────────────────────────┬─────────────────────────┬─────────────────────────────┐
│ Cmd  │ Name                      │ Response Check Requirements   │ Success Criteria         │ Error Handling               │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 0    │ Machine Info              │ - Min 20 bytes                │ Non-zero data            │ Empty response =             │
│      │                           │ - Validate checksum           │                          │ comms failure                │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1    │ Machine State             │ - Min 3 bytes                 │ Valid status byte        │ Length <3 =                  │
│      │                           │ - Byte[2] status code         │ (0-255)                  │ invalid response             │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 256  │ Service Count             │ - Min 4 bytes                 │ Positive integer         │ Zero count =                 │
│      │                           │                               │ in bytes 2-3             │ no services                  │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 259  │ Regular Inspection        │ - Byte[2] = 1                 │ Value 1 in               │ Value 0 =                    │
│      │                           │                               │ status byte              │ test failed                  │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1794 │ Pattern UUID              │ - 16-byte UUID                │ Valid UUID               │ Partial data =               │
│      │                           │                               │ structure                │ incomplete UUID              │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1796 │ Mask Trace (Simple)       │ - Byte[2] = 0                 │ Zero status              │ Non-zero =                   │
│      │                           │                               │                          │ trace rejected               │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1808 │ Mask Trace (Complex)      │ - Byte[2] = 0                 │ Zero status              │ Non-zero =                   │
│      │                           │                               │                          │ invalid coordinates          │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1797 │ Layout Data               │ - Min 2 bytes                 │ First 2 bytes            │ Header mismatch =            │
│      │                           │                               │ match command            │ corruption                   │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1798 │ Embroidery Info           │ - Min 10 bytes                │ Contains stitch          │ Missing fields =             │
│      │                           │                               │ count + dimensions       │ partial info                 │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1799 │ Embroidery Monitor        │ - Real-time updates           │ Valid progress %         │ Negative progress =          │
│      │                           │                               │ in byte[3]               │ error                        │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1800 │ Delete Embroidery         │ - Any response                │ Non-empty ack            │ Empty response =             │
│      │                           │                               │                          │ deletion failed              │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1801 │ Set Needle Mode           │ - No explicit check           │ Machine status           │ Timeout =                    │
│      │                           │                               │ reflects change          │ command ignored              │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1802 │ Send UUID                 │ - Byte[2] = 0                 │ Zero status              │ Non-zero =                   │
│      │                           │                               │                          │ UUID rejected                │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1803 │ Resume Flag               │ - Byte[2] = 1                 │ Value 1 =                │ Value 0 =                    │
│      │                           │                               │ resumable                │ cannot resume                │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1804 │ Resume Embroidery         │ - Byte[2] = 0                 │ Zero status              │ Non-zero =                   │
│      │                           │                               │                          │ resume failed                │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1806 │ Start Sewing              │ - Machine state change         │ State transitions        │ State remains                │
│      │                           │                               │ to "running"             │ idle = failure               │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 1807 │ Hoop Avoidance            │ - State machine update        │ Safety features          │ No state change =            │
│      │                           │                               │ activated                │ activation failed            │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 2048 │ Origin Point              │ - 4 coordinate bytes          │ Valid position           │ Zero coordinates =           │
│      │                           │                               │ values                   │ not calibrated               │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 3072 │ Reset Settings            │ - Byte[2] = 0                 │ Zero status              │ Non-zero =                   │
│      │                           │                               │                          │ reset incomplete             │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 3073 │ Send Host Settings        │ - Byte[2] = 0                 │ Zero status +            │ Checksum mismatch =          │
│      │                           │                               │ checksum match           │ bad config                   │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 3074 │ Machine Settings          │ - Structure match             │ Valid settings           │ Invalid format =             │
│      │                           │                               │ structure                │ parse error                  │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 4608 │ Prepare Transfer          │ - Byte[2] = 0                 │ Zero status +            │ Non-zero =                   │
│      │                           │                               │ ready flag               │ transfer rejected            │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 4609 │ Data Packet               │ - No direct response          │ Subsequent progress      │ Progress stalls =            │
│      │                           │                               │ updates                  │ packet loss                  │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 4864 │ Clear Error               │ - Error log empty             │ Subsequent error         │ Errors persist =             │
│      │                           │                               │ queries empty            │ clear failed                 │
├──────┼───────────────────────────┼───────────────────────────────┼─────────────────────────┼─────────────────────────────┤
│ 4865 │ Error Log                 │ - Header match 0x4865         │ Valid error codes        │ Invalid header =             │
│      │                           │                               │ + timestamps             │ corrupt log                  │
└──────┴───────────────────────────┴───────────────────────────────┴─────────────────────────┴─────────────────────────────┘
'''

'''
| Cmd   | Name                   | Response Check Requirements                          | Success Criteria                   | Error Handling                    |
|-------|------------------------|------------------------------------------------------|------------------------------------|------------------------------------|
| 0     | Machine Info           | - Min 20 bytes - Validate checksum                   | Non-zero data                      | Empty response = comms failure     |
| 1     | Machine State          | - Min 3 bytes - Byte[2] status code                  | Valid status byte (0-255)          | Length <3 = invalid response       |
| 256   | Service Count          | - Min 4 bytes                                        | Positive integer in bytes 2-3      | Zero count = no services           |
| 259   | Regular Inspection     | - Byte[2] = 1                                        | Value 1 in status byte             | Value 0 = test failed              |
| 1794  | Pattern UUID           | - 16-byte UUID                                       | Valid UUID structure               | Partial data = incomplete UUID     |
| 1796  | Mask Trace (Simple)    | - Byte[2] = 0                                        | Zero status                        | Non-zero = trace rejected          |
| 1808  | Mask Trace (Complex)   | - Byte[2] = 0                                        | Zero status                        | Non-zero = invalid coordinates     |
| 1797  | Layout Data            | - Min 2 bytes                                        | First 2 bytes match command        | Header mismatch = corruption       |
| 1798  | Embroidery Info        | - Min 10 bytes                                       | Contains stitch count + dimensions | Missing fields = partial info      |
| 1799  | Embroidery Monitor     | - Real-time updates                                  | Valid progress % in byte[3]        | Negative progress = error          |
| 1800  | Delete Embroidery      | - Any response                                       | Non-empty ack                      | Empty response = deletion failed   |
| 1801  | Set Needle Mode        | - No explicit check                                  | Machine status reflects change     | Timeout = command ignored          |
| 1802  | Send UUID              | - Byte[2] = 0                                        | Zero status                        | Non-zero = UUID rejected           |
| 1803  | Resume Flag            | - Byte[2] = 1                                        | Value 1 = resumable                | Value 0 = cannot resume            |
| 1804  | Resume Embroidery      | - Byte[2] = 0                                        | Zero status                        | Non-zero = resume failed           |
| 1806  | Start Sewing           | - Machine state change                               | State transitions to "running"     | State remains idle = failure       |
| 1807  | Hoop Avoidance         | - State machine update                               | Safety features activated          | No state change = activation failed|
| 2048  | Origin Point           | - 4 coordinate bytes                                 | Valid position values              | Zero coordinates = not calibrated  |
| 3072  | Reset Settings         | - Byte[2] = 0                                        | Zero status                        | Non-zero = reset incomplete        |
| 3073  | Send Host Settings     | - Byte[2] = 0                                        | Zero status + checksum match       | Checksum mismatch = bad config     |
| 3074  | Machine Settings       | - Structure match                                    | Valid settings structure           | Invalid format = parse error       |
| 4608  | Prepare Transfer       | - Byte[2] = 0                                        | Zero status + ready flag           | Non-zero = transfer rejected       |
| 4609  | Data Packet            | - No direct response                                 | Subsequent progress updates        | Progress stalls = packet loss      |
| 4864  | Clear Error            | - Error log empty                                    | Subsequent error queries empty     | Errors persist = clear failed      |
| 4865  | Error Log              | - Header match 0x4865                                | Valid error codes + timestamps     | Invalid header = corrupt log       |

'''


'''
Le caratteristiche GATT estratte dal codice sono le seguenti:

Servizio GATT:

    UUID: a76eb9e0-f3ac-4990-84cf-3a94d2426b2b

Caratteristiche GATT:

    UUID: A76EB9E1-F3AC-4990-84CF-3A94D2426B2B

        Proprietà: Read

    UUID: A76EB9E2-F3AC-4990-84CF-3A94D2426B2B

        Proprietà: Write

Queste caratteristiche vengono utilizzate rispettivamente per la lettura (ReadCharacteristic) e la scrittura (WriteCharacteristic) dei dati su un dispositivo BLE.
'''


'''
calculate the time based on the index
    public static int ConvertPP1EmbPointToMin(int pointCount)
    {
      if (pointCount <= 1)
        return 0;
      double num = Math.Ceiling((double) ((pointCount - 1) * 150 + 3000) / 60000.0);
      return num < 1.0 ? 1 : (int) num;
    }
'''
# max_write_without_response_size
from enum import Enum

import asyncio
from os import wait
import sys
from itertools import count, takewhile, batched
from typing import Iterator
from time import sleep
from dataclasses import dataclass
import struct
from loguru import logger
from typing import Callable, Self, ClassVar
from uuid import UUID



from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from pytest import param

MAIN_SERVICE_UUID = "a76eb9e0-f3ac-4990-84cf-3a94d2426b2b"
READ_CHAR_UUID = "A76EB9E1-F3AC-4990-84CF-3A94D2426B2B"
WRITE_CHAR_UUID = "A76EB9E2-F3AC-4990-84CF-3A94D2426B2B"

class SewingMachineStatus(Enum):
    Initial = 0
    LowerThread = 1
    SewingWaitNoData = 16  # 0x10
    SewingWait = 17        # 0x11
    SewingDataReceive = 18 # 0x12
    MaskTraceLockWait = 32 # 0x20
    MaskTraceing = 33      # 0x21
    MaskTraceFinish = 34   # 0x22
    Sewing = 48            # 0x30
    SewingFinish = 49      # 0x31
    SewingInterruption = 50# 0x32
    ThreadChange = 64      # 0x40
    Pause = 65             # 0x41
    Stop = 66              # 0x42
    HoopAvoidance = 80     # 0x50
    RLReceived = 97         # 0x61
    none = 221             # 0xDD
    TryConnecting = 255    # 0xFF
    HoopAvoidanceing = 81  # 0x51
    RLReceiving = 96       # 0x60

    # @classmethod
    # def from_bytes(cls, data):
    #     logger.trace(data)

    #     logger.trace(int.from_bytes(data,byteorder="little"))
    #     machine_status = cls(int.from_bytes(data,byteorder="little"))
    #     logger.trace("Converted: 0x{:02X} to SewingMachineStatus.{}({})", data, machine_status.name, machine_status.value)
    #     return machine_status

'''
+-------+------------------------+-------------------------------------+------------------------------------+------------------------------------+
| Cmd   | Name                   | Response Check Requirements         | Success Criteria                   | Error Handling                     |
|-------|------------------------|-------------------------------------|------------------------------------|------------------------------------|
| 0     | Machine Info           | - Min 20 bytes - Validate checksum  | Non-zero data                      | Empty response = comms failure     |
| 1     | Machine State          | - Min 3 bytes - Byte[2] status code | Valid status byte (0-255)          | Length <3 = invalid response       |
| 256   | Service Count          | - Min 4 bytes                       | Positive integer in bytes 2-3      | Zero count = no services           |
| 259   | Regular Inspection     | - Byte[2] = 1                       | Value 1 in status byte             | Value 0 = test failed              |
| 1794  | Pattern UUID           | - 16-byte UUID                      | Valid UUID structure               | Partial data = incomplete UUID     |
| 1796  | Mask Trace (Simple)    | - Byte[2] = 0                       | Zero status                        | Non-zero = trace rejected          |
| 1808  | Mask Trace (Complex)   | - Byte[2] = 0                       | Zero status                        | Non-zero = invalid coordinates     |
| 1797  | Layout Data            | - Min 2 bytes                       | First 2 bytes match command        | Header mismatch = corruption       |
| 1798  | Embroidery Info        | - Min 10 bytes                      | Contains stitch count + dimensions | Missing fields = partial info      |
| 1799  | Embroidery Monitor     | - Real-time updates                 | Valid progress % in byte[3]        | Negative progress = error          |
| 1800  | Delete Embroidery      | - Any response                      | Non-empty ack                      | Empty response = deletion failed   |
| 1801  | Set Needle Mode        | - No explicit check                 | Machine status reflects change     | Timeout = command ignored          |
| 1802  | Send UUID              | - Byte[2] = 0                       | Zero status                        | Non-zero = UUID rejected           |
| 1803  | Resume Flag            | - Byte[2] = 1                       | Value 1 = resumable                | Value 0 = cannot resume            |
| 1804  | Resume Embroidery      | - Byte[2] = 0                       | Zero status                        | Non-zero = resume failed           |
| 1806  | Start Sewing           | - Machine state change              | State transitions to "running"     | State remains idle = failure       |
| 1807  | Hoop Avoidance         | - State machine update              | Safety features activated          | No state change = activation failed|
| 2048  | Origin Point           | - 4 coordinate bytes                | Valid position values              | Zero coordinates = not calibrated  |
| 3072  | Reset Settings         | - Byte[2] = 0                       | Zero status                        | Non-zero = reset incomplete        |
| 3073  | Send Host Settings     | - Byte[2] = 0                       | Zero status + checksum match       | Checksum mismatch = bad config     |
| 3074  | Machine Settings       | - Structure match                   | Valid settings structure           | Invalid format = parse error       |
| 4608  | Prepare Transfer       | - Byte[2] = 0                       | Zero status + ready flag           | Non-zero = transfer rejected       |
| 4609  | Data Packet            | - No direct response                | Subsequent progress updates        | Progress stalls = packet loss      |
| 4864  | Clear Error            | - Error log empty                   | Subsequent error queries empty     | Errors persist = clear failed      |
| 4865  | Error Log              | - Header match 0x4865               | Valid error codes + timestamps     | Invalid header = corrupt log       |
+-------+------------------------+-------------------------------------+------------------------------------+------------------------------------+
'''
class MachineCommand(Enum):
    MACHINE_INFO = 0
    MACHINE_STATE = 1
    SERVICE_COUNT = 256
    REGULAR_INSPECTION = 259
    PATTERN_UUID = 1794
    MASK_TRACE_SIMPLE = 1796
    MASK_TRACE_COMPLEX = 1808
    LAYOUT_DATA = 1797
    EMBROIDERY_INFO = 1798
    EMBROIDERY_MONITOR = 1799
    DELETE_EMBROIDERY = 1800
    SET_NEEDLE_MODE = 1801
    SEND_UUID = 1802
    RESUME_FLAG = 1803
    RESUME_EMBROIDERY = 1804
    START_SEWING = 1806
    HOOP_AVOIDANCE = 1807
    ORIGIN_POINT = 2048
    RESET_SETTINGS = 3072
    SEND_HOST_SETTINGS = 3073
    MACHINE_SETTINGS = 3074
    PREPARE_TRANSFER = 4608
    DATA_PACKET = 4609
    CLEAR_ERROR = 4864
    ERROR_LOG = 4865

    def to_bytes(self):
        machine_command = bytearray(self.value.to_bytes(2,byteorder='big'))
        logger.trace("Converted: MachineCommand.{}({}) to bytearray 0x{}", self.name, self.value, machine_command.hex())
        return machine_command

class FrameType(Enum):
    Frame70 = 0
    Frame100 = 1

#TODO
class FootHeightVaule(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


"""
| Byte Offset | Lunghezza | Campo        | Tipo    | Note                                       |
|-------------|-----------|--------------|---------|--------------------------------------------|
| 0           | 1         | auto_cut     | Bool    | 1 for True, 0 for False                    |
| 1           | 1         | jumping_cut  | Bool    | 1 for True, 0 for False                    |
| 2           | 1         | buzzer       | Bool    | 1 for True, 0 for False                    |
| 3           | 1         | foot_height  | Enum    | 1 = LOW, 2 = MEDIUM, 3 = HIGH              |
| 4           | 2         | sewing_speed | Int16   | Little-endian short (2 bytes)              |
"""
@dataclass
class MachineSetting:
    auto_cut: bool
    jumping_cut: bool
    buzzer: bool
    foot_height: FootHeightVaule
    sewing_speed: int

    def to_bytes(self) -> bytearray:
        byte_list = bytearray()

        # Pack AutoCut (1 byte, boolean as 1 or 0)
        byte_list.append(1 if self.auto_cut else 0)
        
        # Pack JumpingCut (1 byte, boolean as 1 or 0)
        byte_list.append(1 if self.jumping_cut else 0)
        
        # Pack Buzzer (1 byte, always 1 for True)
        byte_list.append(1 if self.buzzer else 0)
        
        # Pack FootHeight (1 byte, enum value)
        byte_list.append(self.foot_height.value)
        
        # Pack SewingSpeed (2 bytes, short little-endian)
        byte_list.extend(struct.pack('<h', self.sewing_speed))

        return byte_list

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        # Ensure data is at least 6 bytes
        if len(data) < 6:
            raise ValueError("Insufficient data length for MachineSetting")

        # Unpack AutoCut (1 byte)
        auto_cut = data[0] == 1
        
        # Unpack JumpingCut (1 byte)
        jumping_cut = data[1] == 1
        
        # Unpack Buzzer (1 byte)
        buzzer = data[2] == 1
        
        # Unpack FootHeight (1 byte)
        foot_height = FootHeightVaule(data[3])  # Convert byte to Enum
        
        # Unpack SewingSpeed (2 bytes, short little-endian)
        sewing_speed = struct.unpack('<h', data[4:6])[0]

        return cls(auto_cut, jumping_cut, buzzer, foot_height, sewing_speed)


"""
+-------------+-----------+------------------------+------------+-----------------------------+
| Byte Offset | Lunghezza | Campo                  | Tipo       | Note                        |
+-------------+-----------+------------------------+------------+-----------------------------+
| 0           | 1         | AutoCutValue           | byte       |                             |
| 1           | 1         | JumpingCutValue        | byte       |                             |
| 2           | 9         | SerialNumber           | ASCII      |                             |
| 11          | 1         | No                     | byte       | esadecimale                 |
| 12          | 4         | ProductId              | uint32     |                             |
| 16          | 6         | MacAddress             | byte[6]    | formato MAC                 |
| 22          | 2         | SoftwareMinorVersion   | int16      | diviso per 100              |
| 24          | 2         | BlueToothVersion       | int16      |                             |
| 26          | 1         | Model                  | byte       |                             |
| 27          | 1         | OEM                    | byte       |                             |
| 28          | 1         | IsSupportMonitor       | byte       |                             |
| 29          | 2         | EmbMaxWidth            | int16      |                             |
| 31          | 2         | EmbMaxHeight           | int16      |                             |
| 33          | 2         | (Ignorato?)            | ?          |                             |
| 35          | 2         | SoftwareVersionSuffix  | int16      | accodato come stringa       |
| 37          | 2         | (Ignorato?)            | ?          |                             |
| 39          | 11        | ModelCode              | ASCII      |                             |
+-------------+-----------+------------------------+------------+-----------------------------+

"""
# @dataclass
# class MachineInfo:
#     software_version: int
#     auto_cut: int
#     jumping_cut: int
#     buzzer: int
#     foot_height: int
#     serial_number: str
#     no: int
#     product_id: int
#     mac_address: str
#     bluetooth_version: int
#     model: int
#     oem: int
#     is_support_monitor: int
#     emb_max_width: int
#     emb_max_height: int
#     model_code: str

#     @classmethod
#     def from_bytes(cls, info_bytes: bytes):
#         if len(info_bytes) < 50:
#             raise ValueError("Info bytes length must be at least 50 bytes")
#         logger.trace("Converting {} bytes into MachineInfo dataclass", len(info_bytes))
#         #unpacked = struct.unpack("<H4B9sB I 6s H B B B H H 6x 11s", info_bytes)
#         unpacked = struct.unpack("<??9sBI6BhhBBBhh2xh2x11s", info_bytes)

#         software_version = unpacked[0]
#         auto_cut = unpacked[1:5]
#         jumping_cut = unpacked[1:5]
#         buzzer = unpacked[1:5]
#         foot_height = unpacked[1:5]
#         serial_number = unpacked[5]
#         no = unpacked[6]
#         product_id = unpacked[7]
#         #mac_address = ":".join(f"{b:02X}" for b in unpacked[8])
#         mac_address = unpacked[8]
#         bluetooth_version = unpacked[9]
#         model, oem, is_support_monitor = unpacked[10:13]
#         emb_max_width, emb_max_height = unpacked[13:15]
#         model_code = unpacked[15]


#         return cls(
#             software_version, auto_cut, jumping_cut, buzzer, foot_height,
#             serial_number, no, product_id, mac_address, bluetooth_version,
#             model, oem, is_support_monitor, emb_max_width, emb_max_height, model_code
#         )

#     def to_machine_setting(self) -> MachineSetting:
#         """
#         Convert the current MachineInfo instance to a MachineSetting instance
#         based on matching field names, with type conversions for bool and enum.
#         """
#         return MachineSetting(
#             auto_cut=bool(self.auto_cut),  # Convert to boolean
#             jumping_cut=bool(self.jumping_cut),  # Convert to boolean
#             buzzer=bool(self.buzzer),  # Convert to boolean
#             foot_height=FootHeightVaule(self.foot_height),  # Convert to FootHeightVaule enum
#             sewing_speed=400  # Example static value for sewing speed, can be customized if needed
#         )

"""
+-------------+-----------+------------------------+------------+-----------------------------+
| Byte Offset | Lunghezza | Campo                  | Tipo       | Note                        |
+-------------+-----------+------------------------+------------+-----------------------------+
| 0           | 1         | AutoCut                | Bool       |                             |
| 1           | 1         | SoftwareVersion        | Short      | Majour = /100 minor=reminder|            |
| 3           | 9         | SerialNumber           | String     |                             |
| 16          | 6         | MacAddress             | String     | hex                         |
| 24          | 1         | BlueToothVersion       | Int8       |                             |
| 26          | 1         | Model                  | Int8       |                             |
| 27          | 1         | OEM                    | Int8       |                             |
| 28          | 1         | IsSupportMonitor       | Bool       |                             |
| 29          | 2         | MaxWidth               | Int16      |                             |
| 31          | 2         | MaxHeight              | Int16      |                             |
| 39          | 11        | ModelCode              | String     |                             |
+-------------+-----------+------------------------+------------+-----------------------------+
"""
@dataclass
class MachineInfo:
    AutoCut: bool
    SoftwareVersion: int
    SerialNumber: str
    MacAddress: str
    BlueToothVersion: int
    Model: int
    OEM: int
    IsSupportMonitor: bool
    MaxWidth: int
    MaxHeight: int
    ModelCode: str

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        if len(data) < 50:
            raise ValueError("Data is too short to parse DeviceInfoV4")

        unpacked = struct.unpack_from(
            '<? B 9s 5x 6s 2x b x bb? hh xxx 11s', data
        )

        (
            AutoCut,
            SoftwareVersion,
            serial_raw,
            mac_raw,
            BlueToothVersion,
            Model,
            OEM,
            IsSupportMonitor,
            MaxWidth,
            MaxHeight,
            model_code_raw
        ) = unpacked

        SerialNumber = serial_raw.decode('utf-8', errors='ignore').strip('\x00')
        MacAddress = ':'.join(f'{b:02X}' for b in mac_raw)
        ModelCode = model_code_raw.decode('utf-8', errors='ignore').strip('\x00')

        return cls(
            AutoCut,
            SoftwareVersion,
            SerialNumber,
            MacAddress,
            BlueToothVersion,
            Model,
            OEM,
            IsSupportMonitor,
            MaxWidth,
            MaxHeight,
            ModelCode
        )

"""
+-------------+-----------+---------------+----------+-----------------------------+
| Byte Offset | Lunghezza | Campo         | Tipo     | Note                        |
|-------------|-----------|---------------|----------|-----------------------------|
| 0           | 2         | size_left     | Int16    |                             |
| 2           | 2         | size_top      | Int16    |                             |
| 4           | 2         | size_right    | Int16    |                             |
| 6           | 2         | size_bottom   | Int16    |                             |
| 8           | 2         | total_time    | Int16    | Total estimated time (min?) |
| 10          | 2         | total_stitches| UInt16   | Total stitch count          |
| 12          | 2         | speed         | Int16    | Max/Current speed setting   |
+-------------+-----------+---------------+----------+-----------------------------+
"""
@dataclass
class EmbroideryInfo:
    size_left: int
    size_top: int
    size_right: int
    size_bottom: int
    total_time: int
    total_stitches: int
    speed: int

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        if len(data) < 14:
            raise ValueError("Insufficient data length: expected at least 14 bytes")
        
        # '<' = little-endian, h = Int16, H = UInt16
        unpacked = struct.unpack('<hhhhhhHh', data[:14])
        return cls(
            size_left=unpacked[0],
            size_top=unpacked[1],
            size_right=unpacked[2],
            size_bottom=unpacked[3],
            total_time=unpacked[4],
            total_stitches=unpacked[5],
            speed=unpacked[6],
        )


"""
+-------------+-----------+---------------+------------+-----------------------------+
| Byte Offset | Lunghezza | Campo         | Tipo       | Note                        |
+-------------+-----------+---------------+------------+-----------------------------+
| 0           | 2         | serviceCount  | uint32     |                             |
| 2           | 2         | totalCount    | uint32     |                             |
+-------------+-----------+---------------+------------+-----------------------------+
"""
@dataclass
class ServiceInfo:
    service_count: int
    total_count: int

    @classmethod
    def from_bytes(cls, service_bytes: bytes):
        if len(service_bytes) < 8:
            raise ValueError("Service bytes length must be at least 8 bytes")

        service_count,total_count = struct.unpack("<II", service_bytes[:8])

        return cls(service_count, total_count)


"""
+-------------+-----------+---------+--------+-----------------------+
| Byte Offset | Lunghezza | Campo   | Tipo   | Note                  |
|-------------|-----------|---------|--------|-----------------------|
| 0           | 2         | MoveX   | short  |                       |
| 2           | 2         | MoveY   | short  |                       |
| 4           | 2         | SizeX   | short  | Default = 100         |
| 6           | 2         | SizeY   | short  | Default = 100         |
| 8           | 2         | Rotate  | short  |                       |
| 10          | 1         | Filp    | byte   |                       |
| 11          | 1         | Frame   | byte   | Default = Frame100(1) |
+-------------+-----------+---------+--------+-----------------------+
"""
@dataclass
class EmbroideryLayout:
    MoveX: int
    MoveY: int
    SizeX: int = 100
    SizeY: int = 100
    Rotate: int = 0
    Filp: int = 0
    Frame: FrameType = FrameType.Frame100

    def to_bytes(self) -> bytes:
        return struct.pack('<5h2B', self.MoveX, self.MoveY, self.SizeX, self.SizeY, self.Rotate, self.Filp, self.Frame.value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        if len(data) < 12:
            raise ValueError("Data too short to unpack EmbroideryLayout")
        move_x, move_y, size_x, size_y, rotate, filp, frame_byte = struct.unpack('<5h2B', data[:12])
        frame = FrameType(frame_byte)
        return cls(MoveX=move_x, MoveY=move_y, SizeX=size_x, SizeY=size_y, Rotate=rotate, Filp=filp, Frame=frame)


"""
+-------------+-----------+--------------------+----------+----------------------------+
| Byte Offset | Lunghezza | Campo              | Tipo     | Note                       |
|-------------|-----------|--------------------|----------|----------------------------|
| 0           | 2         | current_stitches   | UInt16   | Stitches completed         |
| 2           | 2         | current_time       | Int16    | Time elapsed               |
| 4           | 2         | stop_time          | Int16    | Time while paused/stopped  |
| 6           | 2         | current_stitch_x   | Int16    | Current X coordinate       |
| 8           | 2         | current_stitch_y   | Int16    | Current Y coordinate       |
+-------------+-----------+--------------------+----------+----------------------------+
"""
@dataclass
class EmbroideryMonitorInfo:
    current_stitches: int
    current_time: int
    stop_time: int
    current_stitch_x: int
    current_stitch_y: int

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        if len(data) < 10:
            raise ValueError("Insufficient data length: expected at least 10 bytes")
        
        # Format: <Hhhhh = UInt16, Int16 x 4 (little-endian)
        unpacked = struct.unpack('<Hhhhh', data[:10])
        return cls(
            current_stitches=unpacked[0],
            current_time=unpacked[1],
            stop_time=unpacked[2],
            current_stitch_x=unpacked[3],
            current_stitch_y=unpacked[4],
        )


class EmbroideryMachine:
    def __init__(self, client):
        self.client = client
        #client.connect()

    async def __aenter__(self):
        return self

    async def __aexit__(self, type, value, traceback):
        await self.client.disconnect()

    @property
    def max_size_packet(self) -> int:
        return 500
    # @property
    # async def max_size_packet(self):
    #     return await self.client.services.get_characteristic(WRITE_CHAR_UUID).max_write_without_response_size

    @staticmethod
    def build_cmd(cmd: bytearray , data: bytearray) -> bytearray:
        buffer = cmd
        if data:
            buffer += data
        logger.trace("From: {} and {} -> 0x{}", cmd, data, buffer.hex())
        return buffer

    async def send(self, cmd: bytearray, data: bytearray = b'', response=True) -> None:
        await self.client.write_gatt_char(WRITE_CHAR_UUID, self.build_cmd(cmd,data), response=response)
        logger.trace("BTSend: {}(0x{})", cmd.hex(), data.hex())

    async def receive(self) -> bytearray:
        value = await self.client.read_gatt_char(READ_CHAR_UUID)
        logger.trace("BTReceive: 0x{}",value)
        return value

    async def request(self, cmd: bytearray, data: bytearray = b'') -> bytearray:
        await self.send(cmd,data)
        return await self.receive()

    async def command(self, cmd: bytearray, data: bytearray = b'') -> None:
        await self.send(cmd, data, response=False)
        logger.debug("BT command: 0x{} (data=0x{}))", cmd.hex(), data.hex() )

    async def machine_request(self, cmd: MachineCommand, data: bytearray = b'') -> bytearray:
        response = await self.request(cmd.to_bytes(), data)
        with logger.contextualize(cmd=cmd, data=data, response=response):
            if not response:
                logger.error("No data has returned", cmd.name)
                return b''

            if len(response) < 2:
                logger.error("Response too short, received only: 0x{}", cmd.name, data.hex(), response.hex())

            if cmd.to_bytes() == response[:2]:
                logger.success("MachineCommand.{}(0x{}) -> 0x{}", cmd.name, data.hex(), response.hex())
                return response[2:]

            logger.error("First data section does not match the cmd", cmd.name, data.hex(), response.hex())
        return b''


    @property
    async def machine_info(self) -> MachineInfo:
        if data := await self.machine_request(MachineCommand.MACHINE_INFO):
            return MachineInfo.from_bytes(data)

    @property
    async def service_info(self) -> ServiceInfo:
        if data := await self.machine_request(MachineCommand.SERVICE_COUNT):
            return ServiceInfo.from_bytes(data)

    @property
    async def machine_state(self) -> ServiceInfo:
        if data := await self.machine_request(MachineCommand.MACHINE_STATE):
            return SewingMachineStatus(data[0])

    @property
    async def pattern_uuid(self) -> UUID:
        if data := await self.machine_request(MachineCommand.PATTERN_UUID):
            logger.trace("UUID: 0x{}", data.hex())
            return UUID(bytes=bytes(data))

    @pattern_uuid.setter
    async def pattern_uuid(self, uuid:UUID) -> None:
        data = await self.machine_request(MachineCommand.SEND_UUID, uuid.bytes_le)
        if len(data) > 0 and data[0] == 1:
            logger.success("the UUID: {} was written successfully", uuid)
        logger.error("the UUID: {} failed", uuid)

    @property
    async def can_resume(self) -> bool:
        data = await self.machine_request(MachineCommand.RESUME_FLAG)
        if len(data) > 0:
            flag = data[0] == 1
            logger.success("The embroidery resume flag is: ", flag)
            return flag
        logger.error("Resume embroidery failed")
        return False

    @property
    async def origin(self) -> bytearray:
        data = await self.machine_request(MachineCommand.ORIGIN_POINT)
        logger.success("The origin point is: {}", data)
        return data

    @property
    async def embroidery_info(self) -> EmbroideryInfo:
        data = await self.machine_request(MachineCommand.EMBROIDERY_INFO)
        info = EmbroideryInfo.from_bytes(data)
        return info

    @property
    async def monitor_info(self) -> EmbroideryMonitorInfo:
        data = await self.machine_request(MachineCommand.EMBROIDERY_MONITOR)
        info = EmbroideryMonitorInfo.from_bytes(data)
        return info

    @property
    async def error_logs(self) -> bytearray:
        data = await self.machine_request(MachineCommand.ERROR_LOG)
        logger.info("Machine error logs: {}", str(data))
        return data

    @property
    async def machine_settings(self) -> MachineSetting:
        return self.machine_info.to_machine_setting()

    @machine_settings.setter
    async def machine_settings(self, settings: MachineSetting) -> None:
        await self.machine_request(MachineCommand.MACHINE_SETTINGS, settings.to_bytes())
        logger.success("Apply new settings: {}", settings)

    async def set_stitch_index(self, index: int) -> int:
        await self.machine_request(MachineCommand.SET_NEEDLE_MODE, bytes(index))
        logger.success("Set stitch index to {}",index)

    async def reset_settings(self) -> None:
        data = await self.machine_request(MachineCommand.RESET_SETTINGS)
        if len(data) > 0 and data[0] != 0:
            logger.error("Configuration reset failed")
            return
        logger.success("Configuration reset completed successfully")

    async def clear_error(self) -> None:
        await self.machine_request(MachineCommand.CLEAR_ERROR)
        logger.success("Error cleared")

    async def delete_emboridery(self):
        if not await self.machine_request(MachineCommand.DELETE_EMBROIDERY):
            logger.error("Embroidery deletition failed")
            return
        logger.success("Embroidery deletition completed successfully")
        #TODO: need to check the state change

    async def resume_emboridery(self) -> None:
        data = await self.machine_request(MachineCommand.RESUME_EMBROIDERY)
        if len(data) > 0 and data[0] != 0:
            logger.error("Resume embroidery failed")
            return
        logger.success("Resume embroidery completed successfully")
        #TODO: need to check the state change

    async def start_emboridery(self) -> None:
        data = await self.machine_request(MachineCommand.START_SEWING)
        logger.success("Starting embroidery completed successfully")
        #TODO: need to check the state change

    async def send_layout(self, layout: EmbroideryLayout) -> None:
        await self.machine_request(MachineCommand.LAYOUT_DATA, layout.to_bytes())
        logger.success("Sended layout data")

    async def do_regular_inspection(self) -> None:
        data = await self.machine_request(MachineCommand.REGULAR_INSPECTION)
        if data and data[0] != 1:
            logger.error("Regular inspection failed")
            return
        logger.success("Done regular inspection")

    async def do_hoop_avoidance(self) -> None:
        await self.machine_request(MachineCommand.HOOP_AVOIDANCE)
        logger.success("Sent Hoop avoidence command")

    async def prepare_transfer(self, size: int, checksum: int) -> None:
        data = await self.machine_request(MachineCommand.PREPARE_TRANSFER, b'\03' + size.to_bytes(length=2,byteorder='little') + checksum.to_bytes(length=2,byteorder='little'))
        if data and data[0] != 0:
            logger.error("Preliminary data sending failed")
            return
        logger.success("Sent preliminary data. the machine is expecting {} bytes with checksum 0x{}",size, hex(checksum))

    async def transfer(self, data: bytearray) -> None:
        transfer_size = self.max_size_packet
        checksum = sum(data)
        await self.prepare_transfer(len(data),checksum)
        for index, chunk in enumerate(batched(data,n=transfer_size,strict=False)):
            chunk_checksum = sum(chunk)
            offset = index * len(chunk)
            await self.command(MachineCommand.DATA_PACKET, offset.to_bytes(4,'little') + chunk + chunk_checksum.to_bytes(1,'little'))
        #TODO: Error handling
        while((result := await self.receive()) > 3 and result[2] != 0):
            if result[2] == 2:
                await asyncio.sleep(1)
