# 1802 : Send EmbroideryUUID -> 3 byte, ok if last = 1
# 1803 : GetEmbroideryResumeFlag -> 3 byte, ok if last = 1
# 1804 : SendEmbrodieryResumeCommand -> 3 byte, ok if last = 0
# 1800 : SendEmbrodieryDeleteCommand -> 3 bye, no check
# 1798 : GetEmbrodieryInfo -> get unpacked TODO
# 1799 : GetEmbrodieryMonitorInfo -> get unpacked TODO
# 3073 : SendingHostSettings(data) ->  3 byte, ok if last = 0

# 1807 : SendHoopAvoidance() -> ignored
# 1896 : StartSewing(bool isforceResetMonitoring) -> ignored
# 4864 : ClearError(byte errorcode) -> ignored

# 2048 : GetEmbOrgPoint() -> retun unformatted bytes
# 4865 :

'''
LE Command List (Parameters Required ✔️ / ❌)
Command	Name	Parameters?	Parameter Description
0	Retrieve Machine Information	❌	None
1	Get Machine State	❌	None
256	Retrieve Service Count	❌	None
259	Perform Regular Inspection	❌	None
1794	Request Pattern UUID	❌	None
1796	Execute Mask Trace (Simple)	✔️	Single-byte mask configuration
1808	Execute Mask Trace (Complex)	✔️	Multi-byte trace coordinates
1797	Send Layout Data	✔️	Binary layout configuration (positioning data)
1798	Request Embroidery Info	❌	None
1799	Monitor Embroidery Progress	❌	None
1800	Delete Embroidery Data	❌	None
1801	Set Needle Mode/Stitch Index	✔️	2-byte stitch index (little-endian)
1802	Send Embroidery UUID	✔️	16-byte UUID identifier
1803	Check Resume Flag	❌	None
1804	Resume Embroidery	❌	None
1806	Start Sewing	❌	None
1807	Activate Hoop Avoidance	❌	None
2048	Get Origin Point	❌	None
2816	Start Firmware Update	✔️*	Firmware data packets (implementation not fully shown)
3072	Reset Machine Settings	❌	None
3073	Send Host Settings	✔️	Configuration byte array (machine-specific settings)
3074	Retrieve Machine Settings	❌	None
4608	Prepare Data Transfer	✔️	[3] = file type, [4-7] = total length, [8-9] = checksum
4609	Send Data Packet	✔️	[0-3] = offset, [4-N] = data chunk, [last byte] = checksum
4864	Clear Error Log	✔️	Single-byte error code to clear
4865	Retrieve Error Log	❌	None

Key Parameter Patterns:

    Data Transfer Commands (4608/4609) require structured payloads:

        4608: [Type][Total Length][Checksum]

        4609: [Offset][Data Chunk][Checksum]

    Configuration Commands use raw byte arrays:

        Layout (1797): Machine-specific positioning data

        Host Settings (3073): Custom configuration bytes

    UUID Handling requires 16-byte identifiers:

        Sent as raw bytes (1802)

        Received as byte array (1794)

    Mask Trace has two modes:

        Simple (1796): Single-byte activation

        Complex (1808): Coordinate data package

    Error Handling uses single-byte codes:

        ClearError requires specific error code byte
'''
'''
    public const short MachinInfoCommand = 0;
    public const short MachinStateCommand = 1;
    public const short ServiceCountCommand = 256;
    public const short RegularInspectionCommand = 259;
    private const short PatternUUIDRequestCommand = 1794;
    private const short MaskTraceCommand = 1796;
    private const short MaskTraceCommand1 = 1808;
    private const short LayoutSendCommand = 1797;
    private const short EmbSewingInfoRequestCommand = 1798;
    private const short PatternSewingInfoCommand = 1799;
    private const short EmbSewingDataDeleteCommand = 1800;
    private const short NeedleModeInstructionsCommand = 1801;
    private const short SetSetingRestCommandt = 3072;
    private const short SetSetingSendCommandt = 3073;
    public const short MachinSettingInfoCommand = 3074;
    private const short EmbUUIDSendCommand = 1802;
    private const short ResumeFlagRequestCommand = 1803;
    private const short ResumeCommand = 1804;
    private const byte ResumeEnableFlag = 1;
    private const short HoopAvoidanceCommand = 1807;
    private const short StartSewingCommand = 1806;
    public const short SendDataInfoCommand = 4608;
    public const short SendDataCommand = 4609;
    public const short FirmUpdateStartCommand = 2816;
    private const short ClearErrorCommad = 4864;
    private const short ErrorLogReplyCommad = 4865;
    private const short EmbOrgPointCommad = 2048;
'''

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
This is the layout, we send it before the job
namespace Asura.Core.Models
{
  public class BLEJobLayout
  {
    public short MoveX;
    public short MoveY;
    public short SizeX = 100;
    public short SizeY = 100;
    public short Rotate;
    public byte Filp;
    public byte Frame = 1;

    public byte[] ToBytes()
    {
      return Enumerable.ToArray<byte>(((IEnumerable<byte>) BitUtil.GetBytes(true, this.MoveX, this.MoveY, this.SizeX, this.SizeY, this.Rotate)).Concat<byte>(this.Filp, this.Frame));
    }

    public void SetFrame(BLEJobLayout.BLEFrame frame) => this.Frame = (byte) frame;

    public enum BLEFrame : byte
    {
      Frame70,
      Frame100,
    }
  }
}

'''

'''
Used in GetEmbrodieryInfo
    public void UpdateEmbroideryInfo(byte[] data)
    {
      this.EmbSizeLeft = BitConverter.ToInt16(data, 0);
      this.EmbSizeTop = BitConverter.ToInt16(data, 2);
      this.EmbSizeRight = BitConverter.ToInt16(data, 4);
      this.EmbSizeBottom = BitConverter.ToInt16(data, 6);
      this.EmbTotalTime = BitConverter.ToInt16(data, 8);
      this.EmbTotalStitches = BitConverter.ToUInt16(data, 10);
      this.EmbSpeed = BitConverter.ToInt16(data, 12);
    }

    
Used inUpdateEmbroideryMonitorInfo
    public void UpdateEmbroideryMonitorInfo(byte[] data)
    {
      this.EmbCurrentStitches = BitConverter.ToUInt16(data, 0);
      this.EmbCurrentTime = BitConverter.ToInt16(data, 2);
      this.EmbStopTime = BitConverter.ToInt16(data, 4);
      this.CurrentStitchX = BitConverter.ToInt16(data, 6);
      this.CurrentStitchY = BitConverter.ToInt16(data, 8);
      Action monitorStatusUpdated = this.MonitorStatusUpdated;
      if (monitorStatusUpdated == null)
        return;
      monitorStatusUpdated();
    }
'''
'''
private Task<bool> Write(short cmd, params byte[] data)
    {
      return Task.Run<bool>((Func<Task<bool>>) (async () =>
      {
        try
        {
          if (!this.isConnect || this.gatt == null)
            return false;
          if (!this.gatt.Connect())
          {
            this.gatt.Disconnect();
            return false;
          }
          BluetoothGattService service = this.gatt.GetService(UUID.FromString("a76eb9e0-f3ac-4990-84cf-3a94d2426b2b"));
          if (service == null)
          {
            this.gatt.Disconnect();
            return false;
          }
          this.isWriteSuccess = false;
          this.writeSignal.Reset();
          byte[] _data = Enumerable.ToArray<byte>(((IEnumerable<byte>) BitUtil.GetBytes(cmd)).Concat<byte>(data));
          if (!await MainThread.InvokeOnMainThreadAsync<bool>((Func<bool>) (() =>
          {
            try
            {
              BluetoothGattCharacteristic characteristic = service.GetCharacteristic(UUID.FromString("A76EB9E2-F3AC-4990-84CF-3A94D2426B2B"));
              if (characteristic == null || characteristic.Properties != GattProperty.Write)
              {
                this.gatt.Disconnect();
                return false;
              }
              if (Build.VERSION.SdkInt >= BuildVersionCodes.Tiramisu)
                return this.gatt.WriteCharacteristic(characteristic, _data, 2) == 0;
              characteristic.SetValue(_data);
              characteristic.WriteType = GattWriteType.Default;
              return this.gatt.WriteCharacteristic(characteristic);
            }
            catch
            {
              return false;
            }
          })))
          {
            this.gatt.Disconnect();
            return false;
          }
          this.writeSignal.WaitOne(TimeSpan.FromSeconds((double) this.GattTimeout));
          return this.isWriteSuccess;
        }
        catch
        {
          return false;
        }
      }));
    }
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



from dataclasses import dataclass
from enum import Enum
import struct


'''
    private const int FEED_DATA = 1;
    private const int CUT_DATA = 2;
    private const int COLOR_END = 3;
    private const int DATA_END = 5;
'''

'''
XXXXXXXX XXXXXFFF YYYYYYYY YYYYYfff

X little endian X coordinate, absolute
F flag for COLOR(3) end or DATA end(5)
Y little endian Y coordinate, absolute
f if feed=1, if cut = 2 , jump = feed+cut =
'''
class Section(Enum):
    END = 5
    END_COLOR = 3

class Operation(Enum):
    STITCH = 0
    FEED = 1
    CUT = 2
    JUMP = 3



@dataclass
class Command:
    x: int
    y: int
    op: Operation
    se: Section
    
    @classmethod
    def from_byte(cls, data):
        x,y = struct.unpack('<hh',data)
       
        return cls(
            x >> 3,
            y >> 3,
            Section(x & 0x07),
            Operation(y & 0x07)
        )
    
    @classmethod
    def from_bytes(cls, data):
        cmds = []
        for x,y in struct.iter_unpack('<hh',data):
            cmds.append(
                cls(
                    x >> 3,
                    y >> 3,
                    Section(x & 0x07),
                    Operation(y & 0x07)
                ))
        return cmds

    def to_byte(self):
        return struct.pack('<hh',(self.x << 3) | self.se, (self.y << 3) | self.op )
    
    @classmethod
    def to_bytes(cls, list):
        data = b''
        for point in list:
          data += point.to_byte()
        return data
    

import struct
from dataclasses import dataclass

