import universe
import os
import random
import torch
import time
import asyncio
import secrets
from typing import Optional, List, Tuple, Any
from mpc_py import start_coordinator, connect_party
from fss import random_gen, Gen_SC, Gen_DPF, Gen_mult

BIND = "10.110.144.225:5000"
COORD_ID = (1 << 64) - 1  # internal id for coordinator

async def main():
    start_time = time.time()
    coord = await start_coordinator(BIND, n=2)
    print("[Coordinator] ready")
    await coord.broadcast({"kind": "init"}, tag="init")
    #await coord.send(to = 0, obj = {"kind": "cmd", "from": "coordinator", "msg": [1,2,3,4,5,6,7,8,9]}, tag="cmd")

    p_length = 10
    E = [(i, j) for i in range(0, p_length) for j in range(i+1, p_length)]
    message_to_p0, message_to_p1 = [[],[], [],[], [],[]], [[],[], [],[], [],[]]
    random_values = []
    start_time = time.time()
    for _ in range(p_length):
        r_u32 = random_gen()
        r0_u32 = random_gen()
        r1_u32 = universe.sub(r_u32, r0_u32)
        message_to_p0[0].append(r0_u32)
        message_to_p1[0].append(r1_u32)
        random_values.append(r_u32)
    for e in E:
        i,j = e
        k0, k1 = Gen_SC(randmask_u32=universe.sub(random_values[i],random_values[j]))
        message_to_p0[1].append(k0)
        message_to_p1[1].append(k1)

    for i in range(p_length):
        r_u32 = random_gen()
        #print('mask',r_u32)
        r0_u32 = random_gen()
        r1_u32 = universe.sub(r_u32, r0_u32)
        k0, k1 = Gen_DPF(alpha_u32=r_u32, beta_u32=int(1))
        message_to_p0[2].append(r0_u32)
        message_to_p1[2].append(r1_u32)
        message_to_p0[3].append(k0)
        message_to_p1[3].append(k1)

    q = torch.nn.Softmax(dim=1)(torch.rand(1,p_length))
    q = sorted(q.tolist()[0])
    #print('dealer computed', q)
    start_time = time.time()
    for i in range(p_length):
        for j in range(p_length):
            rx_u32, ry_u32 = random_gen(), random_gen()
            k0, k1 = Gen_mult(rx_u32=rx_u32, ry_u32=ry_u32)
            # already masked value
            masked_q_j = universe.add(ry_u32,universe.float2fix(q[j]))
            message_to_p0[4].append(masked_q_j)
            message_to_p1[4].append(masked_q_j)
            # save mult keys
            message_to_p0[5].append(k0)
            message_to_p1[5].append(k1)
    await coord.send(to = 0, obj = {"kind": "cmd", "from": "coordinator", "msg": message_to_p0}, tag="cmd")
    await coord.send(to = 1, obj = {"kind": "cmd", "from": "coordinator", "msg": message_to_p1}, tag="cmd")

    end_time = time.time()
    print(f"offline running time: {end_time - start_time:.6f} seconds")
    print("[Coordinator] init sent; routing (Ctrl-C to stop)")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        print("[Coordinator] shutting down")

if __name__ == "__main__":
    asyncio.run(main())
