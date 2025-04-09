import pytest
from sendpp1.machine import EmbroideryMachine, MachineCommand, SewingMachineStatus
import bleak
import asyncio

from loguru import logger
import sys

BROTHER_MAC="1a:4b:e8"

logger.add(sys.stdout, level="TRACE", colorize=True, backtrace=True, diagnose=True)



class MockGATTClient:
  def __init__(self):
    self.buffer = b''

  def __ainit__(self):
    self.buffer = b''

  async def write_gatt_char(self,uuid, data,*, response=False):
    match MachineCommand(int.from_bytes(data[:2],byteorder='big')):
      case MachineCommand.MACHINE_STATE:
        self.buffer = data[:2]
        self.buffer += SewingMachineStatus.SewingWaitNoData.value.to_bytes()
        self.buffer += b'\x00'

  async def read_gatt_char(self,uuid):
    return self.buffer

  async def __aenter__(self):
    return self

  async def __aexit__(self,exc_type,exc_val,exc_tb):
    pass

  def disconnect(self):
    pass

@pytest.fixture
def mock_client(monkeypatch):
    def mock(*args, **kwargs):
        return MockGATTClient()
    monkeypatch.setattr("bleak.BleakClient", mock )

@pytest.mark.asyncio
async def test_machine_get_state(mock_client):

  async with bleak.BleakClient("device_address") as client:
    with EmbroideryMachine(client) as e:
      state = await e.machine_state
