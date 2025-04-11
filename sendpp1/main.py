import asyncio
import click
from click import ParamType
from click.shell_completion import CompletionItem
from bleak import BleakScanner, BleakClient
from machine import EmbroideryMachine
from time import sleep
from loguru import logger
import sys

BROTHER_MAC="1a:4b:e8"

logger.add(sys.stdout, level="TRACE", colorize=True, backtrace=True, diagnose=True)

class BleUUID(ParamType):
    name = "BleUUID"

    def shell_complete(self, ctx, param, incomplete):
        return [ CompletionItem(device.address) for device in scan() ]

@click.group()
def cli():
    pass

@click.command()
def scan():
    """Scan for BLE devices."""
    async def scan_ble_devices():
        print("Scanning for BLE devices...")
        try:
            devices = await BleakScanner.discover()
        except:
            print("No interfaces found")
            return []
        brother_devices = []
        for device in devices:
            if(BROTHER_MAC in device.address):
                click.echo(f"Found device: {device.name} - {device.address}")
                brother_devices.append[device]
        return brother_devices

    asyncio.run(scan_ble_devices())

@click.command()
@click.argument("device_address")
def read(device_address):
    """Read a characteristic from a BLE device."""
    async def read_characteristic():
        async with BleakClient(device_address) as client:
            #await client.connect()
            service = await client.services
            if await client.is_connected():
                print(f"Connected to {device_address}")
                async with EmbroideryMachine(client) as e:
                    print("strating shenanigans")
                    while True:
                        #info = await e.machine_info
                        state = await e.machine_state
                        #print(info)
                        print(state)
                        state = await e.get_error_logs()
                        print(state)
                        await asyncio.sleep(1)

    asyncio.run(read_characteristic())

cli.add_command(scan)
cli.add_command(read)

if __name__ == "__main__":
    cli()
