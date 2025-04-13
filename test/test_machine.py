from ast import Assert
import pytest
from sendpp1.machine import EmbroideryMachine, MachineCommand, SewingMachineStatus
import bleak
import asyncio
import uuid
from unittest.mock import MagicMock, AsyncMock
from loguru import logger
import sys


DUT_MAC="DE:AD:BE:EF"

logger.add(sys.stdout, level="TRACE", colorize=True, backtrace=True, diagnose=True)

def build_response(command: MachineCommand, *data: bytearray):
  return command.to_bytes() + b''.join(data)

def mock_gatt_response(fixture, command: MachineCommand, *data: bytearray):
  fixture.read_gatt_char.return_value = command.to_bytes() + b''.join(data)


def yield_transactions(*responses):
  for x in responses:
    yield x

@pytest.fixture
def mock_bt_response(request,mocker):
    # Patch the original class
    mock_client_class = mocker.patch('bleak.BleakClient')
    mock_instance = AsyncMock()
    mock_instance.__aenter__.return_value = mock_instance  # Return itself when entered
    mock_instance.disconnect = MagicMock()
    mock_instance.read_gatt_char.return_value = next(request.param)
    mock_client_class.return_value = mock_instance
    yield mock_instance



@pytest.mark.parametrize('mock_bt_response', [
    yield_transactions(build_response(MachineCommand.MACHINE_STATE, SewingMachineStatus.SewingWaitNoData.value.to_bytes(), b'\00'))
  ]
  ,indirect=True)
@pytest.mark.asyncio
async def test_get_state(mock_bt_response):
  async with bleak.BleakClient(DUT_MAC) as client:
    with EmbroideryMachine(client) as e:
      data = await e.machine_state
      assert data == SewingMachineStatus.SewingWaitNoData


@pytest.mark.parametrize('mock_bt_response', [yield_transactions(build_response(MachineCommand.PATTERN_UUID,uuid.UUID('2acc7752-16f5-11f0-9cd2-0242ac120002').bytes))],indirect=True)
@pytest.mark.asyncio
async def test_machine_get_uuid(mock_bt_response):
  async with bleak.BleakClient(DUT_MAC) as client:
    with EmbroideryMachine(client) as e:
      id = await e.pattern_uuid
      assert id == uuid.UUID('2acc7752-16f5-11f0-9cd2-0242ac120002')

def get_transaction():
  response = [
    build_response(MachineCommand.PREPARE_TRANSFER,b'\0'),
    build_response(MachineCommand.DATA_PACKET,b'\x02'),
    build_response(MachineCommand.DATA_PACKET,b'\x00'),
  ]
  for x in response:
    yield x

@pytest.mark.parametrize('mock_bt_response', [yield_transactions(
    build_response(MachineCommand.PREPARE_TRANSFER,b'\0'),
    build_response(MachineCommand.DATA_PACKET,b'\x02'),
    build_response(MachineCommand.DATA_PACKET,b'\x00'),)],indirect=True)
@pytest.mark.asyncio
async def test_machine_transfer(mock_bt_response):
  async with bleak.BleakClient(DUT_MAC) as client:
    with EmbroideryMachine(client) as e:
      await e.transfer(b'\x01'*20)


"0x000000684734503635383838376101bc2a7094ddf81a4be800640065020101e803e8030100000000003838385230303530323031"
@pytest.mark.parametrize('mock_bt_response', [yield_transactions(
      build_response(MachineCommand.MACHINE_INFO,bytes.fromhex("000000684734503635383838376101bc2a7094ddf81a4be800640065020101e803e8030100000000003838385230303530323031")),
    )]
    ,indirect=True)
@pytest.mark.asyncio
async def test_machine_transfer(mock_bt_response):
  async with bleak.BleakClient(DUT_MAC) as client:
    with EmbroideryMachine(client) as e:
      await e.machine_info