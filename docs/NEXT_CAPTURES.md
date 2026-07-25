# Next Passive Captures

The capture path is now validated with a genuine reconnect trace. The next
useful scenario is an updater-open reconnect differential:

1. Start complete-root-hub USBPcap capture with descriptor injection disabled.
2. Launch `Update.exe` with no arguments.
3. Do not click any control.
4. Disconnect the USB-only VOD700 and wait about three seconds.
5. Reconnect it and wait for Windows `Status=Started`.
6. Leave the updater idle for about 15 seconds.
7. Close it normally and stop the capture.

Compare against `baseline_reconnect.pcapng`, separating standard enumeration
from any updater-originated `0x01`, `0x81`, `0x02`, or `0x82` traffic.

Do not proceed if the updater starts an update, opens firmware/erase material,
requires a button click, or would allow a vendor write. No active request is
authorized by the baseline capture.
