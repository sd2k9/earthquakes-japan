#!/bin/bash
#
# Shell script to call a program, and flag it's execution in case there
# is any output from the program.
# The output is mailed to some location.
# Further calls are then prevented by a status file
#

# *** Settings
PROG_CMD="./weather_info_fetch.py -q"
LOG_FILE="./weather_info_fetch.suspend"
MAIL_CMD="mail"
MAIL_TO_ME="MAILADRESS1"
MAIL_TO_TWITTER="MAILADRESS2"

# Print current time
echo
date


# *** Execute and check for return
if [ -s "$LOG_FILE" ]; then
  # Banned execution
  echo "Further execution prevented, because lockfile $LOG_FILE is non-zero"
  exit
else
  echo "Executing $PROG_CMD ..."
  $PROG_CMD &> $LOG_FILE
fi


# *** Error in execution?
if [ -s "$LOG_FILE" ]; then
  echo "Error encountered!"
  echo "Content of $LOG_FILE:"
  cat $LOG_FILE

  # Mail the message me
  cat $LOG_FILE | $MAIL_CMD -s "Earthquake failing" $MAIL_TO_ME
  # Twitter failure - temporary forward to my mobile phone instead
  # $MAIL_CMD -s "EARTHQUAKE Failing" $MAIL_TO_TWITTER
  cat $LOG_FILE | $MAIL_CMD -s "EARTHQUAKE Failing" $MAIL_TO_TWITTER
else
  # All OK
  echo "Execution OK"
  echo
fi

