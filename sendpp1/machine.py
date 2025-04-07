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
# max_write_without_response_size
from enum import Enum

import asyncio
import sys
from itertools import count, takewhile
from typing import Iterator
from time import sleep
from dataclasses import dataclass
import struct
from loguru import logger

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

MAIN_SERVICE_UUID = "a76eb9e0-f3ac-4990-84cf-3a94d2426b2b"
READ_CHAR_UUID = "A76EB9E1-F3AC-4990-84CF-3A94D2426B2B"
WRITE_CHAR_UUID = "A76EB9E2-F3AC-4990-84CF-3A94D2426B2B"

class SewingMachineStatus(Enum):
    Initial = 0,
    LowerThread = 1,
    SewingWaitNoData = 16,  # 0x10
    SewingWait = 17,        # 0x11
    SewingDataReceive = 18, # 0x12
    MaskTraceLockWait = 32, # 0x20
    MaskTraceing = 33,      # 0x21
    MaskTraceFinish = 34,   # 0x22
    Sewing = 48,            # 0x30
    SewingFinish = 49,      # 0x31
    SewingInterruption = 50,# 0x32
    ThreadChange = 64,      # 0x40
    Pause = 65,             # 0x41
    Stop = 66,              # 0x42
    HoopAvoidance = 80,     # 0x50
    RLReceived = 97,        # 0x61
    none = 221,             # 0xDD
    TryConnecting = 255,    # 0xFF
    HoopAvoidanceing = 81,  # 0x51
    RLReceiving = 96,       # 0x60

    @classmethod
    def from_bytes(cls, data):
        machine_status = cls(int.from_bytes(data,byteorder="big"))
        logger.trace("Converted: 0x{:02X} to SewingMachineStatus.{}({})", data, machine_status.name, machine_status.value)
        return machine_status



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


@dataclass
class MachineInfo:
    software_version: int
    auto_cut: int
    jumping_cut: int
    buzzer: int
    foot_height: int
    serial_number: str
    no: int
    product_id: int
    mac_address: str
    bluetooth_version: int
    model: int
    oem: int
    is_support_monitor: int
    emb_max_width: int
    emb_max_height: int
    model_code: str

    @classmethod
    def from_bytes(cls, info_bytes: bytes):
        if len(info_bytes) < 50:
            raise ValueError("Info bytes length must be at least 50 bytes")

        unpacked = struct.unpack("<H4B9sB I 6s H B B B H H 6x 11s", info_bytes[:50])

        software_version = unpacked[0]
        auto_cut, jumping_cut, buzzer, foot_height = unpacked[1:5]
        serial_number = unpacked[5].decode("ascii").strip()
        no = unpacked[6]
        product_id = unpacked[7]
        mac_address = ":".join(f"{b:02X}" for b in unpacked[8])
        bluetooth_version = unpacked[9]
        model, oem, is_support_monitor = unpacked[10:13]
        emb_max_width, emb_max_height = unpacked[13:15]
        model_code = unpacked[15].decode("ascii").strip()

        return cls(
            software_version, auto_cut, jumping_cut, buzzer, foot_height,
            serial_number, no, product_id, mac_address, bluetooth_version,
            model, oem, is_support_monitor, emb_max_width, emb_max_height, model_code
        )
    
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
from dataclasses import dataclass
from typing import ClassVar
import struct

@dataclass
class BLEDeviceInfo:
    auto_cut: int
    jumping_cut: int
    serial_number: str
    no: int
    product_id: int
    mac_address: str
    sw_minor: float
    bluetooth_version: int
    model: int
    oem: int
    support_monitor: int
    emb_max_width: int
    emb_max_height: int
    sw_suffix: int
    model_code: str

    FORMAT: ClassVar[str] = "<BB9sB I h h B B B h h x h 2x 11s"
    INFO_SIZE: ClassVar[int] = struct.calcsize(FORMAT)  # Should be 50

    @classmethod
    def from_bytes(cls, data: bytes) -> "BLEDeviceInfo":
        if len(data) < cls.INFO_SIZE:
            raise ValueError("Data too short")

        unpacked = struct.unpack(cls.FORMAT, data[:cls.INFO_SIZE])

        (
            auto_cut,
            jumping_cut,
            serial_bytes,
            no,
            product_id,
            sw_minor_raw,
            bluetooth_version,
            model,
            oem,
            support_monitor,
            emb_max_width,
            emb_max_height,
            sw_suffix,
            model_code_bytes
        ) = unpacked

        serial_number = serial_bytes.decode("ascii")
        mac_bytes = data[16:22]
        mac_address = ":".join(f"{b:02X}" for b in mac_bytes)
        sw_minor = round(sw_minor_raw / 100.0, 2)
        model_code = model_code_bytes.decode("ascii").rstrip("\x00")

        return cls(
            auto_cut, jumping_cut, serial_number, no, product_id,
            mac_address, sw_minor, bluetooth_version,
            model, oem, support_monitor,
            emb_max_width, emb_max_height, sw_suffix,
            model_code
        )

    def to_bytes(self) -> bytes:
        serial_bytes = self.serial_number.encode("ascii").ljust(9, b'\x00')
        model_code_bytes = self.model_code.encode("ascii").ljust(11, b'\x00')
        mac_bytes = bytes(int(b, 16) for b in self.mac_address.split(":"))

        # Create a placeholder for the entire structure
        data = bytearray(self.INFO_SIZE)

        # Fill the mac address manually (still necessary, not part of struct)
        data[16:22] = mac_bytes

        struct.pack_into(
            self.FORMAT, data, 0,
            self.auto_cut,
            self.jumping_cut,
            serial_bytes,
            self.no,
            self.product_id,
            int(self.sw_minor * 100),
            self.bluetooth_version,
            self.model,
            self.oem,
            self.support_monitor,
            self.emb_max_width,
            self.emb_max_height,
            self.sw_suffix,
            model_code_bytes
        )

        return bytes(data)



class EmbroideryMachine:
    def __init__(self, client):
        self.client = client
        #client.connect()


    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.client.disconnect()

    @staticmethod
    def build_cmd(cmd: MachineCommand , data: bytearray) -> bytearray:
        buffer = cmd.to_bytes()
        if data:
            buffer += data
        logger.trace("From: {} and {} -> 0x{}", cmd, data, buffer.hex())
        return buffer

    async def send(self, cmd: MachineCommand, data: bytearray = None) -> None:
        await self.client.write_gatt_char(WRITE_CHAR_UUID, self.build_cmd(cmd,data), response=True)
        logger.trace("BTSend: {}(0x{})", cmd.name, data.hex())

    async def receive(self) -> bytearray:
        value = await self.client.read_gatt_char(READ_CHAR_UUID)
        logger.trace("BTReceive: 0x{value:02X}")
        return value

    async def request(self, cmd: MachineCommand, data: bytearray = None) -> bytearray:
        await self.send(cmd,data)
        return await self.receive()
    
    async def command(self, cmd: MachineCommand, data: bytearray = None) -> None:
        await self.send(cmd, data)
        logger.debug("BT command: {}(0x{})",cmd.name, data.hex())

    @property
    async def machine_info(self) -> MachineInfo:
        if info := await self.request(MachineCommand.MACHINE_INFO):
            return MachineInfo.from_bytes(info)
        
    @property
    async def service_info(self) -> ServiceInfo:
        if info := await self.request(MachineCommand.SERVICE_COUNT):
            return ServiceInfo.from_bytes(info)

    @property
    async def machine_state(self) -> ServiceInfo:
        if info := await self.request(MachineCommand.MACHINE_STATE):
            return SewingMachineStatus.from_bytes(info[2])
