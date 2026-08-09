# Sige

Code for our paper **"Hardening Output Privacy for Secure Inference: A Lightweight Realization via Distributed Trust"** (ICDCS 2026).

Sige is a plug-in MIA defense module for MPC-based secure inference. It runs as a post-processing step after secure inference and consists of two protocols: `Sige-sorting` and `Sige-selection`.

## Files

```
dealer.py     # model owner: pre-processing (FSS key generation, correlated randomness)
party0.py     # server P0: online phase
party1.py     # server P1: online phase
fss.py        # FSS building blocks (DPF, DDCF, secure comparison, multiplication)
comm_ut.py    # communication utilities
run.sh        # launcher
```

## 1. Install

```bash
pip install andy-universe
pip install andy-mpc-py
```

## 2. Run

```bash
git clone https://github.com/Wangxinqian/Sige_ICDCS26.git
cd Sige_ICDCS26
bash run.sh
```

`run.sh` frees the ports from any previous run, then starts the dealer, Party 0 and Party 1:

```bash
#!/bin/bash

DEALER_PORT=5000
COMM_PORT=5000

# Check and clean up the dealer port
echo "Cleaning up dealer port ${DEALER_PORT}..."
DEALER_PID=$(lsof -ti tcp:${DEALER_PORT})
if [ -n "$DEALER_PID" ]; then
    echo "Killing process on dealer port: $DEALER_PID"
    kill -9 $DEALER_PID
else
    echo "Dealer port ${DEALER_PORT} is already clean."
fi

# Check and clean up the communication port
echo "Cleaning up comm port ${COMM_PORT}..."
COMM_PID=$(lsof -ti tcp:${COMM_PORT})
if [ -n "$COMM_PID" ]; then
    echo "Killing process on comm port: $COMM_PID"
    kill -9 $COMM_PID
else
    echo "Comm port ${COMM_PORT} is already clean."
fi

# Start the dealer (model owner)
echo "Starting dealer..."
python dealer.py &
sleep 1

# Start Party 0
echo "Starting Party 0..."
python party0.py &
sleep 1

# Start Party 1
echo "Starting Party 1..."
python party1.py &
```

You can also start the three roles manually, one per terminal, in this order:

```bash
python dealer.py
python party0.py
python party1.py
```

The coordinator keeps running after the protocol finishes — press `Ctrl-C` to stop it.

Expected output:

```
[Coordinator] ready
offline running time: 0.010999 seconds
[Coordinator] init sent; routing (Ctrl-C to stop)
online running time: 0.053700 seconds
online running time: 0.058295 seconds
```

## ⚠️ Before you run

**Set your own IP addresses and paths.** The addresses in the code are ours, not yours — you have to change them:

- `dealer.py`: `BIND = "<ip>:<port>"` is the address the coordinator listens on.
- `party0.py` / `party1.py`: the address passed to `connect_party(...)` must point at the dealer.

Two cases:

- **Single machine** (local, Google Colab, one VM): use loopback everywhere, i.e. `127.0.0.1:5000` (or bind with `0.0.0.0:5000`).
- **Multiple machines**: use each host's real IP, and make sure the port is open in the firewall / security group.

Also check any file paths (model, data, output) hard-coded in the scripts and point them at your own directories.

**Start small.** On your first run, set `p_length` (and the other size parameters) to a small value such as 8 or 16. The online cost of `Sige-sorting` grows with `n^2` DDCF evaluations, so a large `p_length` will take a long time and eat a lot of memory on a low-resource machine. Once the pipeline works end to end, scale it up.

## Google Colab

Everything runs on a single VM, so use loopback addresses as above. Then:

```python
!pip install andy-universe
!pip install andy-mpc-py
!git clone https://github.com/Wangxinqian/Sige_ICDCS26.git
%cd Sige_ICDCS26
!bash run.sh
```

Note that Colab is one machine, so it can verify correctness and local compute time, but not the LAN/WAN communication numbers reported in the paper.

## Citation

```bibtex
@inproceedings{wang2026sige,
  title     = {Hardening Output Privacy for Secure Inference: A Lightweight Realization via Distributed Trust},
  author    = {Wang, Xinqian and Liu, Xiaoning and Lai, Shangqi and Yi, Xun and Khalil, Ibrahim and Lam, Kwok-Yan},
  booktitle = {2026 IEEE 46th International Conference on Distributed Computing Systems (ICDCS)},
  pages     = {316--326},
  year      = {2026},
  doi       = {10.1109/2575-8411.2026.00037}
}
```

## Contact

Xinqian Wang — xinqian.wang@rmit.edu.au
