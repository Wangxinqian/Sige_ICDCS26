#!/bin/bash

# 定义需要清理的端口
DEALER_PORT=5000
COMM_PORT=5000

# 检查并清理 dealer_port
echo "Cleaning up dealer port ${DEALER_PORT}..."
DEALER_PID=$(lsof -ti tcp:${DEALER_PORT})
if [ -n "$DEALER_PID" ]; then
    echo "Killing process on dealer port: $DEALER_PID"
    kill -9 $DEALER_PID
else
    echo "Dealer port ${DEALER_PORT} is already clean."
fi

# 检查并清理 comm_port
echo "Cleaning up comm port ${COMM_PORT}..."
COMM_PID=$(lsof -ti tcp:${COMM_PORT})
if [ -n "$COMM_PID" ]; then
    echo "Killing process on comm port: $COMM_PID"
    kill -9 $COMM_PID
else
    echo "Comm port ${COMM_PORT} is already clean."
fi

# 启动 Party 1
echo "Starting dealer..."
python dealer.py &
sleep 1  # 等待 Party 1 完全启动

# 启动 Party 2
echo "Starting Party 0..."
python party0.py &
sleep 1  # 等待 Party 2 完全启动

# 启动 Party 3
echo "Starting Party 1..."
python party1.py &
