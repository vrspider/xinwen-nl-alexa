#!/bin/bash
# Script to install cron job for the xinwen-nl-alexa project.
# It will run main.py every day at 16:00 (4 pm).

WORKDIR="/Users/yuankunma/DEV/Tools/xinwen-nl-alexa"
PYTHON="${WORKDIR}/venv/bin/python"  # adjust if using system python
LOGFILE="${WORKDIR}/cron.log"

# build the cron line
CRONLINE="0 16 * * * cd ${WORKDIR} && ${PYTHON} main.py >> ${LOGFILE} 2>&1"

# install it in the user's crontab (preserves existing entries)
( crontab -l 2>/dev/null; echo "# xinwen-nl-alexa daily run"; echo "${CRONLINE}" ) | crontab -

echo "Cron job installed. Use 'crontab -l' to verify."