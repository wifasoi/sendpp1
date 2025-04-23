import asyncio
import click
from click import ParamType
from click.shell_completion import CompletionItem
from bleak import BleakScanner, BleakClient
from sendpp1.core.machine import EmbroideryMachine, MachineCommand
from time import sleep
from loguru import logger
from uuid import UUID
import sys

# BROTHER_MAC="1a:4b:e8"

# logger.add(sys.stdout, level="TRACE", colorize=True, backtrace=True, diagnose=True)

# class BleUUID(ParamType):
#     name = "BleUUID"

#     def shell_complete(self, ctx, param, incomplete):
#         return [ CompletionItem(device.address) for device in scan() ]

# @click.group()
# def cli():
#     pass

# @click.command()
# def scan():
#     """Scan for BLE devices."""
#     async def scan_ble_devices():
#         print("Scanning for BLE devices...")
#         try:
#             devices = await BleakScanner.discover()
#         except:
#             print("No interfaces found")
#             return []
#         brother_devices = []
#         for device in devices:
#             if(BROTHER_MAC in device.address):
#                 click.echo(f"Found device: {device.name} - {device.address}")
#                 brother_devices.append[device]
#         return brother_devices

#     asyncio.run(scan_ble_devices())

# @click.command()
# @click.argument("device_address")
# def read(device_address):
#     """Read a characteristic from a BLE device."""
#     async def read_characteristic():
#         async with BleakClient(device_address) as client:
#             #await client.connect()
#             #service = client.services
#             if client.is_connected:
#                 print(f"Connected to {device_address}")
#                 async with EmbroideryMachine(client) as e:
#                     print("strating shenanigans")
#                     while True:
#                         info = await e.machine_info
#                         set = await e.machine_settings
#                         #state = await e.machine_state
#                         print(info)
#                         print(set)
#                         set.auto_cut = True
#                         await e.set_machine_settings(set)
#                         #print(state)
#                         # state = await e.error_logs
#                         # print(state)
#                         await asyncio.sleep(1)

#     asyncio.run(read_characteristic())

# cli.add_command(scan)
# cli.add_command(read)

# if __name__ == "__main__":
#     cli()


from sendpp1.core.machine import (
    EmbroideryMachine,
    MachineCommand,
    MachineSetting,
    EmbroideryLayout,
    EmbroideryMonitorInfo,
    WRITE_CHAR_UUID,
    READ_CHAR_UUID,
    FrameType
)

@click.group()
def cli():
    pass

async def connect_and_execute(device, coro_func):
    """Helper function to connect and execute a coroutine."""
    client = BleakClient(device)
    try:
        await client.connect()
        async with EmbroideryMachine(client) as machine:
            return await coro_func(machine)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise click.ClickException(str(e))
    finally:
        await client.disconnect()

# Info retrieval commands
@cli.command()
@click.option('--device', required=True, help='BLE device address')
def get_machine_info(device):
    """Get machine information."""
    async def _get_info(machine):
        return await machine.machine_info
    info = asyncio.run(connect_and_execute(device, _get_info))
    click.echo(info)

@cli.command()
@click.option('--device', required=True, help='BLE device address')
def get_service_info(device):
    """Get service information."""
    async def _get_info(machine):
        return await machine.service_info
    info = asyncio.run(connect_and_execute(device, _get_info))
    click.echo(info)

@cli.command()
@click.option('--device', required=True, help='BLE device address')
def get_machine_state(device):
    """Get machine state."""
    async def _get_state(machine):
        return await machine.machine_state
    state = asyncio.run(connect_and_execute(device, _get_state))
    click.echo(state)

# Pattern UUID commands
@cli.command()
@click.option('--device', required=True, help='BLE device address')
def get_pattern_uuid(device):
    """Get pattern UUID."""
    async def _get_uuid(machine):
        return await machine.pattern_uuid
    uuid = asyncio.run(connect_and_execute(device, _get_uuid))
    click.echo(uuid)

@cli.command()
@click.option('--device', required=True, help='BLE device address')
@click.argument('uuid')
def set_pattern_uuid(device, uuid):
    """Set pattern UUID."""
    async def _set_uuid(machine):
        uuid_obj = UUID(uuid)
        response = await machine.machine_request(MachineCommand.SEND_UUID, uuid_obj.bytes_le)
        if response and response[0] == 1:
            return "UUID set successfully"
        return "Failed to set UUID"
    result = asyncio.run(connect_and_execute(device, _set_uuid))
    click.echo(result)

# Embroidery control commands
@cli.command()
@click.option('--device', required=True, help='BLE device address')
def start_embroidery(device):
    """Start embroidery."""
    async def _start(machine):
        await machine.start_emboridery()
        return "Embroidery started"
    result = asyncio.run(connect_and_execute(device, _start))
    click.echo(result)

@cli.command()
@click.option('--device', required=True, help='BLE device address')
def resume_embroidery(device):
    """Resume embroidery."""
    async def _resume(machine):
        await machine.resume_emboridery()
        return "Embroidery resumed"
    result = asyncio.run(connect_and_execute(device, _resume))
    click.echo(result)

@cli.command()
@click.option('--device', required=True, help='BLE device address')
def clear_error(device):
    """Clear machine errors."""
    async def _clear(machine):
        await machine.clear_error()
        return "Errors cleared"
    result = asyncio.run(connect_and_execute(device, _clear))
    click.echo(result)

# Data transfer commands
@cli.command()
@click.option('--device', required=True, help='BLE device address')
@click.argument('data_file', type=click.File('rb'))
def transfer_data(device, data_file):
    """Transfer data from a file."""
    data = data_file.read()
    async def _transfer(machine):
        await machine.transfer(bytearray(data))
        return "Data transferred successfully"
    result = asyncio.run(connect_and_execute(device, _transfer))
    click.echo(result)

# Add more commands for other methods following the same pattern

@cli.command()
@click.option('--suffix', default="1a:4b:e8", help='MAC address suffix to match (last 3 octets)')
def scan_device(suffix):
    """Scan for BLE devices matching MAC address suffix."""
    async def _scan():
        # Normalize input suffix
        suffix_clean = suffix.strip().lower().replace('-', ':')
        if len(suffix_clean.split(':')) != 3:
            raise click.BadParameter("Suffix must be in format 'XX:XX:XX'")

        click.echo(f"🔍 Scanning for BLE devices (matching suffix {suffix_clean})...")
        devices = await BleakScanner.discover()
        
        found_devices = []
        for d in devices:
            # Get last 3 octets of device MAC
            device_octets = d.address.lower().replace('-', ':').split(':')
            device_suffix = ':'.join(device_octets[-3:])
            
            if device_suffix == suffix_clean:
                found_devices.append(d)

        if found_devices:
            click.secho(f"✅ Found {len(found_devices)} device(s) matching suffix {suffix_clean}", fg='green')
            for d in found_devices:
                click.echo(f"  - {d.address} ({d.name or 'No name'})")
        else:
            click.secho(f"❌ No devices found matching suffix {suffix_clean}", fg='red')

    asyncio.run(_scan())


@cli.command()
@click.option('--device', required=True, help='BLE device address')
def error_logs(device):
    """Retrieve machine error logs in hexadecimal format."""
    async def _get_error_logs(machine):
        return await machine.error_logs
    
    async def _execute():
        logs = await connect_and_execute(device, _get_error_logs)
        if logs:
            # Format as hex bytes with space separation for readability
            hex_logs = ' '.join(f"{b:02x}" for b in logs)
            click.echo(f"Error logs ({len(logs)} bytes): {hex_logs}")
            click.echo(f"\nASCII interpretation: {logs.decode('ascii', errors='replace')}")
        else:
            click.echo("No error logs available")

    asyncio.run(_execute())

@cli.command()
@click.option('--device', required=True, help='BLE device address')
def hoop_avoidance(device):
    """Execute hoop avoidance maneuver on the machine."""
    async def _execute_hoop_avoidance(machine):
        await machine.do_hoop_avoidance()
        return "Hoop avoidance command sent successfully"

    async def _run():
        result = await connect_and_execute(device, _execute_hoop_avoidance)
        click.secho(result, fg='green')
        click.echo("Note: Monitor machine status for completion")

    asyncio.run(_run())


@cli.command()
@click.option('--device', required=True, help='BLE device address')
@click.option('--move-x', required=True, type=int, help='X-axis movement (short)')
@click.option('--move-y', required=True, type=int, help='Y-axis movement (short)')
@click.option('--size-x', type=int, default=100, show_default=True, help='X size (short)')
@click.option('--size-y', type=int, default=100, show_default=True, help='Y size (short)')
@click.option('--rotate', type=int, default=0, show_default=True, help='Rotation angle (short)')
@click.option('--flip', type=click.IntRange(0, 255), default=0, 
             show_default=True, help='Flip setting (0-255)')
@click.option('--frame', type=click.Choice([f.name for f in FrameType] + ["1", "2"]), 
             default="Frame100", show_default=True,
             help='Frame type (name or value)')
def send_layout(device, move_x, move_y, size_x, size_y, rotate, flip, frame):
    """Send embroidery layout parameters to the machine."""
    async def _send_layout(machine):
        # Convert frame input to FrameType enum
        try:
            if frame.isdigit():
                frame_type = FrameType(int(frame))
            else:
                frame_type = FrameType[frame]
        except (KeyError, ValueError):
            raise click.BadParameter(f"Invalid frame value: {frame}")
        
        # Create layout object
        layout = EmbroideryLayout(
            MoveX=move_x,
            MoveY=move_y,
            SizeX=size_x,
            SizeY=size_y,
            Rotate=rotate,
            Filp=flip,
            Frame=frame_type
        )
        
        # Send to machine
        await machine.send_layout(layout)
        return layout

    async def _run():
        try:
            layout = await connect_and_execute(device, _send_layout)
            click.secho("✅ Layout sent successfully", fg='green')
            click.echo("\nLayout Parameters:")
            click.echo(f"  Move X: {layout.MoveX}")
            click.echo(f"  Move Y: {layout.MoveY}")
            click.echo(f"  Size X: {layout.SizeX}")
            click.echo(f"  Size Y: {layout.SizeY}")
            click.echo(f"  Rotation: {layout.Rotate}°")
            click.echo(f"  Flip: {layout.Filp}")
            click.echo(f"  Frame: {layout.Frame.name}")
        except Exception as e:
            click.secho(f"❌ Error sending layout: {str(e)}", fg='red')

    asyncio.run(_run())


if __name__ == '__main__':
    cli()