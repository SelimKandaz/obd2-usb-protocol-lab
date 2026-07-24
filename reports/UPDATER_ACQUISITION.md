# Updater Acquisition Report (Phase 2)

Date: 2026-07-24. **Status: BLOCKED — official updater is behind an account sign-in.**

## Device identification (resolved)
The device is the **ANCEL VOD700**, a multi-system OBD2 scanner. ANCEL is the
consumer brand; **Autophix** is the OEM (matching the device's USB manufacturer
string `Autophix`). The official software is distributed by ANCEL, not Autophix.

- ANCEL VOD700 product page (official):
  `https://www.anceltech.com/product/detail?id=VOD7005984218324582`
- ANCEL download portal (official): `https://www.anceltech.com/download.html`
  (select model **VOD700**)

## What the official download portal returns
The portal's download API (`POST /download/getdown` with `model=VOD700`) returns,
for the VOD700:

| Item                | Availability                                             |
|---------------------|---------------------------------------------------------|
| **Upgrade Software**| **Sign-in required** — button "View Updates" links to `/login.html`, marked *"Available after sign-in"* (padlock). |
| Users Manual (PDF)  | Public — ~48.9 MB (not downloaded; proprietary, not needed). |

So the update software (the executable containing the WinUSB protocol logic we
want to statically analyze) is **gated behind an ANCEL account login**.

## Why this is blocked for automated acquisition
Creating an account and authenticating (entering a password) is a prohibited
action for the assistant. Therefore the gated updater cannot be downloaded
autonomously. This is a genuine owner action.

## Official pages checked
- `https://www.anceltech.com` (home, product tree — no public VOD700 software)
- `https://www.anceltech.com/download.html` (portal; VOD700 upgrade software = sign-in only)
- `https://www.anceltech.com/product/detail?id=VOD7005984218324582` (product page; links manual + portal)
- `https://autophix.com` and `https://autophix.com/support` (OEM site; per-product
  downloads, no VOD700 listing — expected, since VOD700 is ANCEL-branded)

No unofficial mirrors, forums, or third-party sites were used.

## Required owner action
Sign in to the ANCEL account at `https://www.anceltech.com/download.html`, select
**VOD700**, download the **Upgrade Software** package, and place the extracted
folder (or the zip) into `private_samples\updater\` (git-ignored). Then:
```
powershell -ExecutionPolicy Bypass -File scripts\hash_updater_files.ps1 -Path private_samples\updater -OutJson private_samples\updater_inventory.json
```
This starts Phase 3 (static analysis) — which is fully automatable once the files
are present.

## To record once the updater is provided
source page · final download URL · filename · size · SHA-256 · Authenticode
signature + signer + validity · PE architecture · product/file version · company
name · download date.
