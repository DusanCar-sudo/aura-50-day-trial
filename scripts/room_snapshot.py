#!/usr/bin/env python3
"""Consented room-condition snapshot test (still images only).

Takes one still image every N minutes from a visible webcam for a fixed
window and saves it locally with a timestamp. No video, no person
detection, no upload. Requires a consent reference and an explicit typed
confirmation before the first frame is captured.

Usage:
  pip install opencv-python
  python scripts/room_snapshot.py --consent-ref "RELEASE-001 (hotel mgr name)" \
      --room 214 --interval-min 5 --duration-min 120

Stop early: press Ctrl+C, or create a file named STOP in the output folder.
"""
import argparse
import datetime as dt
import pathlib
import sys
import time

import cv2


def now():
    return dt.datetime.now().astimezone()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--consent-ref", required=True,
                   help="reference to the signed consent release")
    p.add_argument("--room", required=True, help="test room label")
    p.add_argument("--interval-min", type=float, default=5)
    p.add_argument("--duration-min", type=float, required=True)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--out", default="room_snapshots")
    a = p.parse_args()

    out = pathlib.Path(a.out) / f"room{a.room}_{now():%Y%m%d_%H%M%S}"
    out.mkdir(parents=True)
    log = out / "log.txt"

    def note(msg):
        line = f"{now().isoformat(timespec='seconds')}  {msg}"
        print(line)
        with log.open("a") as f:
            f.write(line + "\n")

    print("=" * 62)
    print(" CAMERA TEST - STILL IMAGES ONLY")
    print(f" Room: {a.room}   Every {a.interval_min} min for {a.duration_min} min")
    print(f" Consent ref: {a.consent_ref}")
    print(" Post a 'camera active' sign on the door before continuing.")
    print(f" Stop anytime: Ctrl+C, or create {out / 'STOP'}")
    print("=" * 62)
    if input("Type YES to confirm written consent is on file: ").strip() != "YES":
        sys.exit("Not confirmed. No images captured.")

    cam = cv2.VideoCapture(a.camera)
    if not cam.isOpened():
        sys.exit("Cannot open webcam.")

    note(f"START room={a.room} consent_ref={a.consent_ref!r}")
    end = time.time() + a.duration_min * 60
    n = 0
    try:
        while time.time() < end and not (out / "STOP").exists():
            for _ in range(5):  # let exposure settle
                cam.read()
            ok, frame = cam.read()
            if ok:
                n += 1
                path = out / f"{now():%H%M%S}_{n:03d}.jpg"
                cv2.imwrite(str(path), frame)
                note(f"saved {path.name}")
            else:
                note("frame grab failed")
            wake = time.time() + a.interval_min * 60
            while time.time() < min(wake, end) and not (out / "STOP").exists():
                time.sleep(1)
    except KeyboardInterrupt:
        note("stopped by operator")
    finally:
        cam.release()
        note(f"END images={n}. Delete after test unless participants agree otherwise.")


if __name__ == "__main__":
    main()
