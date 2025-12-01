#!/bin/bash
# Launch D' Fake Seeder with system tray

cd /home/daoneill/src/DFakeSeeder || exit

# Launch main application in background
env LOG_LEVEL=DEBUG PYTHONPATH=/home/daoneill/src/DFakeSeeder pipenv run python3 d_fake_seeder/dfakeseeder.py &

# Wait for main app to initialize
sleep 2

# Launch tray application
exec env LOG_LEVEL=DEBUG PYTHONPATH=/home/daoneill/src/DFakeSeeder pipenv run python3 d_fake_seeder/dfakeseeder_tray.py
