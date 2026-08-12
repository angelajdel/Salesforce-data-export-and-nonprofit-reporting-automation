#!/bin/bash
# Double-click this file (or run it from Terminal) to pull fresh Salesforce
# data and open Impact Hub -- no GitHub, no command line typing required
# beyond double-clicking this file.
cd "$(dirname "$0")"
python3 run_local.py
echo ""
echo "Press Enter to close this window..."
read
