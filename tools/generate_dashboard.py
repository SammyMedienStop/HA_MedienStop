#!/usr/bin/env python3
# tools/generate_dashboard.py
# Standalone-Generator (für Profis). Nutzt dieselbe Logik wie der eingebaute
# Button. Echte Gerätenamen kennt dieses Skript außerhalb von HA nicht ->
# es verwendet "Kind n" / "Profil n".
#
#   python3 generate_dashboard.py --children 3 --profiles 2 > mein_dashboard.yaml

import argparse
import importlib.util
import os

_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "ms_dashboard", os.path.join(_here, "..", "dashboard.py")
)
_d = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_d)


def main() -> None:
    ap = argparse.ArgumentParser(description="MedienStop Dashboard-Generator")
    ap.add_argument("--children", type=int, default=2)
    ap.add_argument("--profiles", type=int, default=1)
    args = ap.parse_args()
    print(_d.build_dashboard_yaml(args.children, args.profiles))


if __name__ == "__main__":
    main()
