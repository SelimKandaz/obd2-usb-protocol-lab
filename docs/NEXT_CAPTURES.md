# Next Passive Capture

Do not repeat `baseline_reconnect.pcapng`. The remaining capture is the first
official updater transaction, using `scripts/capture_updater_first_vendor.ps1`:

1. Run the controller elevated with the VOD700 connected and Update.exe closed.
2. When it prints `CAPTURE_ACTIVE — OPEN THE OFFICIAL UPDATER AND STOP BEFORE CLICKING UPDATE`, open the exact official updater with no arguments.
3. Wait for `READY — CLICK UPDATE ONCE NOW`.
4. Click Update exactly once.
5. The controller observes an 18-second bounded post-click window, contains
   Update.exe, and stops USBPcap automatically.

The controller never clicks the UI, injects descriptors, sends a vendor
request, opens firmware/erase material, or continues into an update workflow.
Compare the resulting trace against `baseline_reconnect.pcapng`, excluding
the known endpoint-0 enumeration records before classifying the first vendor
transfer.
