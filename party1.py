import universe
import os
import random
import torch
import time
import asyncio
import secrets
from typing import Optional, List, Tuple, Any
from mpc_py import start_coordinator, connect_party
from comm_ut import wait_for_init, recv_matching_with_pending
from fss import Eval_SC, Eval_DPF, Eval_mult

BIND = "10.110.144.225:5000"
COORD_ID = (1 << 64) - 1  # internal id for coordinator

async def main(p_length):
    idx = 1
    peer_idx = 1 - idx
    me = f"party-{idx+1}"
    peer_name = f"party-{peer_idx+1}"
    party = await connect_party(BIND, idx=idx)

    # Local buffer so early/out-of-order messages aren't lost
    pending: List[Tuple[int, Optional[str], Any]] = []

    # now wait for coordinator's 'cmd'
    frm, tag, obj = await recv_matching_with_pending(party, want_kind="cmd", want_from="coordinator",
        pending=pending, recv_timeout=None,   # or None for indefinite wait
    )
    random_values_sorting, keys_list_sorting, random_values_routing, keys_list_routing, masked_q_mult, keys_list_mult = obj["msg"]

    # Online-1, reveal and mask
    # 1. Initialize share of confidence vectors
    p_length = 400
    E = [(i, j) for i in range(0, p_length) for j in range(i+1, p_length)]
    random_values, keys_list = random_values_sorting, keys_list_sorting
    p_1 = torch.zeros_like(torch.rand(1,p_length))
    p_1 = p_1.tolist()[0]
    start_time = time.time()
    # 2. mask locally
    for i in range(p_length):
        p_1[i] = random_values[i]
    # 3. transmit the message
    await party.send({"kind": "mask", "from": me, "r": p_1}, to=peer_idx)
    _, _, peer_mask_msg = await recv_matching_with_pending(
        party, want_kind="mask", want_from=peer_name, pending=pending, recv_timeout=30.0,)
    p_0 = peer_mask_msg['r']
    # 4. reveal the masked value
    p_hat = []
    for i in range(p_length):
        p_hat.append(universe.add(p_0[i], p_1[i]))

    # Online-2, SHAMP-sorting
    rank = [0 for _ in range(p_length)]
    for k in range(len(E)):
        i,j = E[k]
        p1_result = Eval_SC(key=keys_list[k], input_u32=universe.sub(p_hat[i], p_hat[j]))
        rank[i] = universe.add(rank[i], p1_result)
        rank[j] = universe.add(rank[j], universe.sub(1, p1_result))
    #print(rank)

    # Online-3, DPF routing
    random_values, keys_list = random_values_routing, keys_list_routing
    p_1 = rank
    for i in range(p_length):
        r_u32 = random_values[i]
        p_1[i] = universe.add(p_1[i], r_u32)
    await party.send({"kind": "mask2", "from": me, "r": p_1}, to=peer_idx)
    _, _, peer_mask_msg = await recv_matching_with_pending(
            party, want_kind="mask2", want_from=peer_name, pending=pending, recv_timeout=30.0,)
    p_0 = peer_mask_msg['r']
    rank_hat = []
    for i in range(p_length):
        rank_hat.append(universe.add(p_0[i], p_1[i]))

    m_ij_1_list = []
    for i in range(p_length):
        for j in range(p_length):
            m_ij = Eval_DPF(key=keys_list[i], input_u32=universe.sub(rank_hat[i],j))
            sel_idex = i*p_length + j
            masked_m_ij_1 = universe.add(keys_list_mult[sel_idex][1],m_ij)
            m_ij_1_list.append(masked_m_ij_1)
    await party.send({"kind": "mask3", "from": me, "r": m_ij_1_list}, to=peer_idx)
    _, _, peer_mask_msg = await recv_matching_with_pending(
                party, want_kind="mask3", want_from=peer_name, pending=pending, recv_timeout=30.0,)
    m_ij_0_list = peer_mask_msg['r']

    q_prime = []
    for i in range(p_length):
        q_prime.append(0)
        for j in range(p_length):
            sel_idex = i*p_length + j
            masked_m_ij = universe.add(m_ij_0_list[sel_idex],m_ij_1_list[sel_idex])
            masked_q_j = masked_q_mult[sel_idex]
            # Evaluate Mult
            q_prime_ij = Eval_mult(key=keys_list_mult[sel_idex],masked_x=masked_m_ij,masked_y=masked_q_j)
            q_prime[i] = universe.add(q_prime[i],q_prime_ij)

    #print(q_prime)
    end_time = time.time()
    print(f"online running time: {end_time - start_time:.6f} seconds")




if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="SHAMP")
    ap.add_argument("--vlen", type=int, default=0, help="vector length")
    args = ap.parse_args()
    asyncio.run(main(args.vlen))