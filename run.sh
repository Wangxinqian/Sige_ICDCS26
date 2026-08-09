#!/bin/bash

# Define the ports to be cleaned up
DEALER_PORT=5000
COMM_PORT=5000

# Check and clean up dealer_port
echo "Cleaning up dealer port ${DEALER_PORT}..."
DEALER_PID=$(lsof -ti tcp:${DEALER_PORT})
if [ -n "$DEALER_PID" ]; then
    echo "Killing process on dealer port: $DEALER_PID"
    kill -9 $DEALER_PID
else
    echo "Dealer port ${DEALER_PORT} is already clean."
fi

# Check and clean up comm_port
echo "Cleaning up comm port ${COMM_PORT}..."
COMM_PID=$(lsof -ti tcp:${COMM_PORT})
if [ -n "$COMM_PID" ]; then
    echo "Killing process on comm port: $COMM_PID"
    kill -9 $COMM_PID
else
    echo "Comm port ${COMM_PORT} is already clean."
fi

# Start dealer
echo "Starting dealer..."
python ./Sige_ICDCS26/dealer.py &
sleep 1

# Start Party 0
echo "Starting Party 0..."
python ./Sige_ICDCS26/party0.py &
sleep 1

# Start Party 1
echo "Starting Party 1..."
python ./Sige_ICDCS26/party1.py &
