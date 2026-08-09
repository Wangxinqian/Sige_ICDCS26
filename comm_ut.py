import universe
import os
import random
import torch
import time
import asyncio
import secrets
from typing import Optional, List, Tuple, Any
from mpc_py import start_coordinator, connect_party

# -----------------------------
# Small helpers (buffer + matching)
# -----------------------------
async def wait_for_init(party, pending: List[Tuple[int, Optional[str], Any]], timeout: float = 30.0):
    deadline = asyncio.get_event_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            raise TimeoutError("timed out waiting for coordinator init")
        frm, tag, obj = await asyncio.wait_for(party.recv(), timeout=remaining)
        if frm == COORD_ID and tag == "init" and isinstance(obj, dict) and obj.get("kind") == "init":
            return
        pending.append((frm, tag, obj))  # buffer anything else

async def recv_matching_with_pending(
    party,
    *,
    want_kind: str,
    want_from: str,
    pending: List[Tuple[int, Optional[str], Any]],
    recv_timeout: Optional[float],
):
    # First, scan pending
    for i, (frm, tag, obj) in enumerate(pending):
        if isinstance(obj, dict) and obj.get("kind") == want_kind and obj.get("from") == want_from:
            return pending.pop(i)
    # Then, receive until match
    while True:
        try:
            frm, tag, obj = await (party.recv() if recv_timeout is None
                                   else asyncio.wait_for(party.recv(), timeout=recv_timeout))
        except asyncio.TimeoutError:
            raise TimeoutError(f"timed out waiting for {want_from}'s {want_kind}")
        except RuntimeError as e:
            raise RuntimeError("connection dropped while waiting for message") from e

        if isinstance(obj, dict) and obj.get("kind") == want_kind and obj.get("from") == want_from:
            return (frm, tag, obj)
        pending.append((frm, tag, obj))