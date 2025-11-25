from ast import List
from sendpp1.core.machine import EmbroideryMachine, EmbroideryLayout, EmbroideryBoundingBox
from PySide6.QtStateMachine import QStateMachine, QState
from PySide6.QtWidgets import QObject
import PySide6.QtAsyncio as QtAsyncio
from PySide6.QtAsyncio import QAsyncioFuture, QAsyncioEventLoop, QAsyncioTask
from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import asyncio
from PySide6.QtCore import Qt, Signal, Slot

class PP1ConenctionManager(QObject):
    devices_discovered = Signal(List[BLEDevice])
    disconnected = Signal()
    connected = Signal()
    information_updated = Signal()
    monitor_updated = Signal()
    discovery_finished = Signal()
    no_device_found = Signal()

    def __init__(self):
        self.update_loop = None
        self.machine = None
        self.client = None
        self.sewing_update_loop = None

    async def machine_info(self, every_s: float = 1):
        while self.machine and self.client.is_connected():
            info = await self.machine.machine_info()
            self.information_updated.emit(info)
            asyncio.sleep(every_s)

    async def monitor_info(self, every_s: float = 1):
        while self.machine and self.client.is_connected():
            info = await self.machine.monitor_info()
            self.monitor_updated.emit(info)
            asyncio.sleep(every_s)

    @Slot()
    def scan(self):
        devices = QtAsyncio.run( BleakScanner.find_device_by_filter(
            lambda device, ad_data: device.address.lower().startswith("1a:4b:e8") #Check if it's from brother
            ) )
        if devices:
            self.devices_discovered.emit(devices)
        else:
            self.no_device_found.emit()
        self.discovery_finished.emit()

    @Slot()
    def connect(self, device: BLEDevice|str, timeout: float = 10.0):
        def disconnect_cb(client: BleakClient):
            self.update_loop.cancel()
            client.disconnect()
            self.disconnected.emit(client)
        
        if self.client.is_connected():
            return

        self.client = BleakClient(device, disconnected_callback=disconnect_cb, timeout=timeout)
        QtAsyncio.run( self.client.connect() )

        if not self.client.is_connected():
            return

        self.connected.emit()
        self.machine = EmbroideryMachine(self.client)
        self.update_loop: QAsyncioTask = QAsyncioEventLoop.create_task(self.machine_info)


    @Slot()
    def send_design(self, layout: EmbroideryLayout, mask: EmbroideryBoundingBox, embroidery: bytearray):
        if not self.machine or not self.client.is_connected():
            return
        
        QtAsyncio.run(self.machine.send_layout(layout,mask))
        QtAsyncio.run(self.machine.transfer(embroidery))

    @Slot()
    def start_sewing_monitor(self):
        if not self.machine or not self.client.is_connected():
            return
        if self.sewing_update_loop:
            self.sewing_update_loop.uncance
        self.sewing_update_loop: QAsyncioTask = QAsyncioEventLoop.create_task(self.monitor_info)

    @Slot()
    def start_sewing_monitor(self):
        if not self.machine or not self.client.is_connected():
            return
        self.sewing_update_loop: QAsyncioTask = QAsyncioEventLoop.create_task(self.monitor_info)

    @Slot()
    def stop_sewing_monitor(self):
        if not self.machine or not self.client.is_connected() or not self.sewing_update_loop:
            return
        self.sewing_update_loop.cancel()