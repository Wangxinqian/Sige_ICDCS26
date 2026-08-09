import socket
import universe
import os
import random
import json
import zlib
import torch
import time

def random_sample_split(r_u32):
    r0_u32 = random_gen()
    r1_u32 = universe.sub(r_u32, r0_u32)
    return r0_u32, r1_u32

def random_gen():
    seed = f"{random.getrandbits(128):032x}"
    return universe.convert(bytes.fromhex(seed))

def Gen_DCF(alpha_u32, beta_u32):
    #beta_u32 = universe.float2fix(beta)
    #alpha_u32 = universe.float2fix(alpha)
    alpha_binary_representation = universe.u32_to_binary_list(alpha_u32)
    #hyperparameter
    n = 32
    cw = []
    # Line-2
    s_0 = [f"{random.getrandbits(128):032x}"]
    s_1 = [f"{random.getrandbits(128):032x}"]
    # Line-3
    V_alpha = universe.float2fix(0)
    t_0 = [0]
    t_1 = [1]
    # Line-4
    for i in range(1,n+1):
        # Line-5 & 6
        s_0L, v_0L, t_0L, s_0R, v_0R, t_0R = universe.split_dcf(universe.pnrg_dcf(bytes.fromhex(s_0[i-1])).hex())
        s_1L, v_1L, t_1L, s_1R, v_1R, t_1R = universe.split_dcf(universe.pnrg_dcf(bytes.fromhex(s_1[i-1])).hex())
        t_0L = int(t_0L, 16) % 2
        t_0R = int(t_0R, 16) % 2
        t_1L = int(t_1L, 16) % 2
        t_1R = int(t_1R, 16) % 2
        # Line - 7 & 8 & 9
        if alpha_binary_representation[i-1] == 0:
            s_0Keep, v_0Keep, t_0Keep, s_0Lose, v_0Lose, t_0Lose = s_0L, v_0L, t_0L, s_0R, v_0R, t_0R
            s_1Keep, v_1Keep, t_1Keep, s_1Lose, v_1Lose, t_1Lose = s_1L, v_1L, t_1L, s_1R, v_1R, t_1R
        else:
            s_0Lose, v_0Lose, t_0Lose, s_0Keep, v_0Keep, t_0Keep = s_0L, v_0L, t_0L, s_0R, v_0R, t_0R
            s_1Lose, v_1Lose, t_1Lose, s_1Keep, v_1Keep, t_1Keep = s_1L, v_1L, t_1L, s_1R, v_1R, t_1R
        # Line 10
        s_cw = universe.strhex_xor(s_0Lose,s_1Lose)
        # Line 11, line_11_result=V_CW
        convert_v_0Lose = universe.convert(bytes.fromhex(v_0Lose))
        convert_v_1Lose = universe.convert(bytes.fromhex(v_1Lose))
        line_11_result = universe.sub(convert_v_1Lose, convert_v_0Lose)
        line_11_result = universe.sub(line_11_result, V_alpha)
        if t_1[i-1] == 1:
            line_11_result = universe.neg(line_11_result)
        else:
            pass
        V_cw = line_11_result
        # Line 12 & 13
        if alpha_binary_representation[i-1] == 0: #Lose = R
            pass
        else: #Lose = L
            # beta_u32
            if t_1[i-1] == 1:
                V_cw = universe.sub(V_cw, beta_u32)
            else:
                V_cw = universe.add(V_cw, beta_u32)
        # Line 14
        V_alpha = universe.sub(V_alpha, universe.convert(bytes.fromhex(v_1Keep)))
        V_alpha = universe.add(V_alpha, universe.convert(bytes.fromhex(v_0Keep)))
        if t_1[i-1] == 1:
            V_alpha = universe.sub(V_alpha, V_cw)
        else:
            V_alpha = universe.add(V_alpha, V_cw)
        # Line 15
        #print(t_0L, t_1L, x_binary_representation[i-1])
        t_cwL = t_0L ^ t_1L ^ int(alpha_binary_representation[i-1]) ^ 1
        t_cwR = t_0R ^ t_1R ^ int(alpha_binary_representation[i-1]) ^ 0
        # Line 16
        cw.append([s_cw,V_cw,t_cwL,t_cwR])
        # Line 17
        if t_0[i-1] == 0: # correction not happened
            s_0.append(s_0Keep)
        else: # correction happened
            s_0.append(universe.strhex_xor(s_0Keep,s_cw))
        if t_1[i-1] == 0: # correction not happened
            s_1.append(s_1Keep)
        else: # correction happened
            s_1.append(universe.strhex_xor(s_1Keep,s_cw))
        # Line 18
        if alpha_binary_representation[i-1] == 0:
            #Keep = L
            t_cwKeep = t_cwL
        else:
            #Keep = R
            t_cwKeep = t_cwR
        if t_0[i-1] == 1: # correction happened
            t_0.append(t_0Keep ^ t_cwKeep)
        else: # correction not happened
            t_0.append(t_0Keep)
        if t_1[i-1] == 1: # correction happened
            t_1.append(t_1Keep ^ t_cwKeep)
        else: # correction not happened
            t_1.append(t_1Keep ^ 0)
    # Line 20
    line_20_result = universe.sub(universe.convert(bytes.fromhex(s_1[n])), universe.convert(bytes.fromhex(s_0[n])))
    line_20_result = universe.sub(line_20_result, V_alpha)
    if t_1[n] == 1:
        line_20_result = universe.neg(line_20_result)
    else:
        pass
    cw.append(line_20_result) #cw has the length of 33
    k0 = (0, s_0[0], cw)
    k1 = (1, s_1[0], cw)
    return k0, k1

def Gen_DDCF(alpha_u32, beta1_u32, beta2_u32):
    beta_u32 = universe.sub(beta1_u32, beta2_u32)
    #this is nive implementation
    S_0 = random_gen()
    S_1 = universe.sub(beta2_u32, S_0)
    k0, k1 = Gen_DCF(alpha_u32, beta_u32)
    return (k0, S_0), (k1, S_1)

def Gen_SC(randmask_u32):
    # Line 1
    y_u32 = universe.neg(randmask_u32)
    # Line 2
    z1_u32 = universe.u32_mod_31(y_u32)
    # Line 3
    y_msb_u32 = universe.u32_msb(y_u32)
    # The values of beta1_u32, beta1_u32 are either 1: u32 or 0: u32
    beta1_u32 = 1 ^ y_msb_u32 #universe.float2fix(1 ^ y_msb_u32)
    beta2_u32 = 0 ^ y_msb_u32 #universe.float2fix(0 ^ y_msb_u32)
    # Line 4
    k0, k1 = Gen_DDCF(alpha_u32=z1_u32, beta1_u32=beta1_u32, beta2_u32=beta2_u32)
    return k0, k1

def Gen_DPF(alpha_u32, beta_u32):
    #hyperparameter
    n = 32
    cw = []
    alpha_binary_representation = universe.u32_to_binary_list(alpha_u32)
    # Line - 2
    s_0 = [f"{random.getrandbits(128):032x}"]
    s_1 = [f"{random.getrandbits(128):032x}"]
    # Line - 3
    t_0 = [0]
    t_1 = [1]
    # Line-4
    for i in range(1,n+1):
        # Line - 5
        s_0L, t_0L, s_0R, t_0R = universe.split_dpf(universe.pnrg_dpf(bytes.fromhex(s_0[i-1])).hex())
        s_1L, t_1L, s_1R, t_1R = universe.split_dpf(universe.pnrg_dpf(bytes.fromhex(s_1[i-1])).hex())
        t_0L = int(t_0L, 16) % 2
        t_0R = int(t_0R, 16) % 2
        t_1L = int(t_1L, 16) % 2
        t_1R = int(t_1R, 16) % 2
        # Line - 6 & 7 & 8
        if alpha_binary_representation[i-1] == 0:
            s_0Keep, t_0Keep, s_0Lose, t_0Lose = s_0L, t_0L, s_0R, t_0R
            s_1Keep, t_1Keep, s_1Lose, t_1Lose = s_1L, t_1L, s_1R, t_1R
        else:
            s_0Lose, t_0Lose, s_0Keep, t_0Keep = s_0L, t_0L, s_0R, t_0R
            s_1Lose, t_1Lose, s_1Keep, t_1Keep = s_1L, t_1L, s_1R, t_1R
        # Line 9
        s_cw = universe.strhex_xor(s_0Lose,s_1Lose)
        # Line 10
        t_cwL = t_0L ^ t_1L ^ int(alpha_binary_representation[i-1]) ^ 1
        t_cwR = t_0R ^ t_1R ^ int(alpha_binary_representation[i-1])
        # Line 11
        cw.append([s_cw, t_cwL, t_cwR])
        # Line 12
        if t_0[i-1] == 0: # correction not happened
            s_0.append(s_0Keep)
        else:
            s_0.append(universe.strhex_xor(s_0Keep,s_cw))
        if t_1[i-1] == 0: # correction not happened
            s_1.append(s_1Keep)
        else: # correction happened
            s_1.append(universe.strhex_xor(s_1Keep,s_cw))
        # Line 13
        # first, let's generate variable t_cwKeep
        if alpha_binary_representation[i-1] == 0:
            #Keep = L
            t_cwKeep = t_cwL
        else:
            #Keep = R
            t_cwKeep = t_cwR
        if t_0[i-1] == 1: # correction happened
            t_0.append(t_0Keep ^ t_cwKeep)
        else: # correction not happened
            t_0.append(t_0Keep)
        if t_1[i-1] == 1: # correction happened
            t_1.append(t_1Keep ^ t_cwKeep)
        else: # correction not happened
            t_1.append(t_1Keep)
        # Line 14, end
    line_15_result = universe.sub(beta_u32, universe.convert(bytes.fromhex(s_0[n])))
    line_15_result = universe.add(line_15_result, universe.convert(bytes.fromhex(s_1[n])))
    if t_1[n] == 1:
        line_15_result = universe.neg(line_15_result)
    else:
        pass
    cw.append(line_15_result) #cw has the length of 33
    k0 = (0, s_0[0], cw)
    k1 = (1, s_1[0], cw)
    return k0, k1

def Gen_mult(rx_u32, ry_u32):
    # Line 1
    rx0_u32, rx1_u32 = random_sample_split(rx_u32)
    # Line 2
    ry0_u32, ry1_u32 = random_sample_split(ry_u32)
    # Line 3
    rxy_u32 = universe.mult(rx_u32, ry_u32)
    rxy0_u32, rxy1_u32 = random_sample_split(rxy_u32)
    return (0, rx0_u32, ry0_u32, rxy0_u32), (1, rx1_u32, ry1_u32, rxy1_u32)


def Eval_mult(key, masked_x, masked_y):
    b, rxb_u32, ryb_u32, rxyb_u32 = key
    return universe.sub(universe.add(b*universe.mult(masked_x,masked_y),rxyb_u32),universe.add(universe.mult(masked_x,ryb_u32),universe.mult(masked_y,rxb_u32)))

def Eval_DPF(key, input_u32):
    n = 32
    # Line 1
    b, s_b_0, cw = key
    party_s_b = [s_b_0]
    input_binary_representation = universe.u32_to_binary_list(input_u32)
    party_t_b = [b]
    # Line 2
    for i in range(1,n+1):
        # Line 3
        s_cw, t_cwL, t_cwR = cw[i-1]
        # Line 4 & 5
        s_hatL, t_hatL, s_hatR, t_hatR = universe.split_dpf(universe.pnrg_dpf(bytes.fromhex(party_s_b[i-1])).hex())
        t_hatL = int(t_hatL, 16) % 2
        t_hatR = int(t_hatR, 16) % 2
        if party_t_b[i-1] == 1:
            s_L = universe.strhex_xor(s_hatL, s_cw)
            t_L = t_hatL ^ t_cwL
            s_R = universe.strhex_xor(s_hatR, s_cw)
            t_R = t_hatR ^ t_cwR
        else:
            s_L = s_hatL
            t_L = t_hatL
            s_R = s_hatR
            t_R = t_hatR
        # Line 6 & 7
        if input_binary_representation[i-1] == 0:
            party_s_b.append(s_L)
            party_t_b.append(t_L)
        else:
            party_s_b.append(s_R)
            party_t_b.append(t_R)
    # Line 10
    if party_t_b[n] == 1:
        party_share_b = universe.add(universe.convert(bytes.fromhex(party_s_b[n])), cw[n])
    else:
        party_share_b = universe.convert(bytes.fromhex(party_s_b[n]))
    if b == 1:
        party_share_b = universe.neg(party_share_b)
    return party_share_b

def Eval_DCF(key, input_u32):
    n = 32
    # Line 1
    b, s_b_0, cw = key
    party_s_b = [s_b_0]
    #input_u32 = universe.float2fix(input)
    input_binary_representation = universe.u32_to_binary_list(input_u32)
    party_V = 0
    party_t_b = [b]

    # Line 2
    for i in range(1,n+1):
        # Line 3
        s_cw,V_cw,t_cwL,t_cwR = cw[i-1]
        # Line 4
        s_hatL, v_hatL, t_hatL, s_hatR, v_hatR, t_hatR = universe.split_dcf(universe.pnrg_dcf(bytes.fromhex(party_s_b[i-1])).hex())
        t_hatL = int(t_hatL, 16) % 2
        t_hatR = int(t_hatR, 16) % 2
        # Line 5 & 6
        if party_t_b[i-1] == 1:
            s_L = universe.strhex_xor(s_hatL, s_cw)
            t_L = t_hatL ^ t_cwL
            s_R = universe.strhex_xor(s_hatR, s_cw)
            t_R = t_hatR ^ t_cwR
        else:
            s_L = s_hatL
            t_L = t_hatL
            s_R = s_hatR
            t_R = t_hatR
        # Line 7 & 8 & 9 & 10
        if input_binary_representation[i-1] == 0:
            line_7_result = universe.convert(bytes.fromhex(v_hatL))
            party_s_b.append(s_L)
            party_t_b.append(t_L)
        else:
            line_7_result = universe.convert(bytes.fromhex(v_hatR))
            party_s_b.append(s_R)
            party_t_b.append(t_R)
        if party_t_b[i-1] == 1:
            line_7_result = universe.add(line_7_result, V_cw)
        if b == 0:
            party_V = universe.add(party_V, line_7_result)
        else:
            party_V = universe.sub(party_V, line_7_result)
    # Line 13
    line_13_result = universe.convert(bytes.fromhex(party_s_b[n]))
    if party_t_b[n]:
        line_13_result = universe.add(line_13_result, cw[n])
    if b == 0:
        party_V = universe.add(party_V, line_13_result)
    else:
        party_V = universe.sub(party_V, line_13_result)
    return party_V

def Eval_DDCF(key, input_u32):
    key_b, S_b = key
    result = Eval_DCF(key=key_b, input_u32=input_u32)
    return universe.add(result, S_b)

def Eval_SC(key, input_u32):
    z0_u32 = universe.u32_mod_31(input_u32)
    a = (2**31)-1
    m_32 = Eval_DDCF(key, universe.sub(a, z0_u32))
    b = key[0][0] # key -> Eval_DDCF's key -> Eval_DCF's key
    result = b * universe.u32_msb(input_u32)
    result = universe.add(result, m_32)
    result = universe.sub(result, (2*universe.u32_msb(input_u32)*m_32)%(2**32))
    return universe.sub(b, result)