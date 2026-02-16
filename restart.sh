#!/bin/bash
# Restart the bot

./stop.sh
sleep 1
./start.sh
echo ""
./status.sh
