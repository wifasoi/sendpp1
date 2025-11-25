sendpp1
-------
This project whant to substitute the android application for the Brother Skitch PP1.

This is more a collection of notes in python form, that a well built project... right now.

Abstraction library
-------------------
in src/sendpp1/core resideds the heart of the project, and RE-ENG effort. There is a main.py with some Vibe Coded cli utility for quick test.

in src/sendpp1/core/machine.py 


How comunication works
++++++++++++++++++++++
The Brother Skitch PP1 "uses" Bluetooth Low energy protocol with just two main carateristics:
* UUID: A76EB9E1-F3AC-4990-84CF-3A94D2426B2B [Read channel]
* UUID: A76EB9E2-F3AC-4990-84CF-3A94D2426B2B [Write channel]

This is used like a serial connection. You write in the Write "channel" and the pp1 will respond with data in the read channel.
The PP1 has a timeout of 3 seconds (more or less), it will disconnect you if yoi don't keep sending some commands, the application by default polls the machine state each second.

Here a list of commands that I exstracted by watching the comunication via wireshark and a bit of vibe:

| Cmd   | Name                   | Response Check Requirements                          | Success Criteria                   | Error Handling                     |
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

Stitch data
+++++++++++
In src/sendpp1/pyembroidery there is the code to convert embroidery data to the pp1 strange format. This is non tested yet on the machine.
Each command is 32 bit LE format like:

XXXXXXXX XXXXXFFF YYYYYYYY YYYYYfff

X little endian X coordinate, absolute
F flag for COLOR(3) end or DATA end(5)
Y little endian Y coordinate, absolute
f if feed=1, if cut = 2 , jump = feed+cut

This is yet to be verified.

the parameter of starting position scale and rotation of each point is sent via a separate command before the job is run.

GUI
---
I started to work on a gui in qt. Right now is not very functional, it just a way to the the widget and how to integrate BT comunication in qt.