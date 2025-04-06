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
    None = 221,             # 0xDD
    TryConnecting = 255,    # 0xFF
    HoopAvoidanceing = 81,  # 0x51
    RLReceiving = 96,       # 0x60

    @classmethod
    def from_bytes(cls, data):
        return cls(int.from_bytes(data))



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


class EmbroideryMachine:
    def __init__(self, client):
        self.client = client
        client.connect()

        self.machine_info = self.getMachineInfo()

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.client.disconnect()

    @staticmethod
    def build_cmd(cmd, data):
        return cmd.into_bytes().append(data)

    async def send(self, cmd, data=None):
        return await self.client.write_gatt_char(WRITE_CHAR_UUID, self.build_cmd(cmd,data), response=False)

    async def receive(self):
        return await self.client.read_gatt_char(READ_CHAR_UUID)

    async def request(self, cmd, data=None):
        await self.send(cmd,data)
        return await self.receive()
    
    async def command(self, cmd, data=None):
        await self.send(cmd, data)

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
            return SewingMachineStatus.from_bytes(info)