from zksk import Secret, DLRep
from zksk.primitives.dl_notequal import DLNotEqual
from functools import reduce

def stmt(public_params, private_params, candidates):
    """Constructs the statement for the ZK proofs in Vote and Obfuscate

    Args: 
        public_params (tuple): public parameters
        private_params (tuple): private parameters
        candidate (int): the number of candidates
i
    Returns:
        full_stmt (tuple): the statement for the ZK proofs in Vote and Obfuscate
    
    """
    g, pk_T, pk_vs, upk, ct_v, ct_lv, ct_lid, ct_i, c0, c1, ct_bar_v, ct_bar_vv = public_params
    r_v, lv, r_lv, r_lid, sk_id, sk_vs = private_params
    R1_range_stmt0, R1_range_stmt1, R1_enc_stmt = [], [], [] 

    #tricks to make the zksk library happy
    one = Secret(value=1)
    neg_c0 = (-1)*c0

    #----------
    #RELATION 1
    #----------

    #PROOF OF VOTE ENCRYPTION  (correctness)
    #(i) proves that each encrypted vote is either 0 or 1
    for i in range(candidates):
        #encryption of 0
        R1_range_stmt0.append(DLRep(ct_v[i][0], r_v*g) & DLRep(ct_v[i][1], r_v*pk_T))
        #encryption of 1
        R1_range_stmt1.append(DLRep(ct_v[i][0], r_v*g) & DLRep(ct_v[i][1] - g, r_v*pk_T))

    #(ii) proves that the sum of all encrypted votes is either 0 or 1 
    elements_c0, elements_c1 = list(map(lambda x: x[0], ct_v)), list(map(lambda x: x[1], ct_v))
    product_c0, product_c1 = reduce(lambda x, y: x + y, elements_c0), reduce(lambda x, y: x + y, elements_c1)
    exp1, exp2= candidates*g, candidates*pk_T
    #encryption of 0
    R1_enc_sum_stmt0 = DLRep(product_c0, exp1*r_v) & DLRep(product_c1, exp2*r_v)
    #encryption of 1
    R1_enc_sum_stmt1 = DLRep(product_c0, exp1*r_v) & DLRep(product_c1 - g, exp2*r_v)

    #flattening of the or-proofs as required by the zksk library and making it also more efficient 
    #instead of proving (R1_range_stmt0_c_0 | R1_range_stmt_1_c_0) & ... & (R1_range_stmt0_c_i | R1_range_stmt_1_c_i) & (R1_enc_sum_stm0 | R1_enc_sum_stm0) 
    #we prove (R1_range_stmt0_c_0 & ... & R1_range_stmt0_c_i & R1_enc_sum_stm0) |  ... | (R1_range_stmt_c_1 & ... & R1_range_stmt0_c_i & R1_enc_sum_stmt1) ) 
    for i in range(candidates):
        if i==0:
            #statement for a vote for the first candidate (1 0 ...  0)  
            R1_enc_stmt.append(R1_enc_sum_stmt1 & R1_range_stmt1[i] & reduce(lambda x, y: x & y, R1_range_stmt0[i+1:]))
        elif i==candidates-1:
            #statement for a vote for the last candidate (0 0 ... 1) 
            R1_enc_stmt.append(R1_enc_sum_stmt1 & R1_range_stmt1[i] & reduce(lambda x, y: x & y, R1_range_stmt0[:i])) 
            #statement for a vote for any other candidate (0 ... 1 ... 0) 
        else: R1_enc_stmt.append(R1_enc_sum_stmt1 & R1_range_stmt1[i] & reduce(lambda x, y: x & y, R1_range_stmt0[:i]) & reduce(lambda x, y: x & y, R1_range_stmt0[i+1:])) 
    #statement for a vote for abstention (0 0 ... 0) 
    R1_enc_stmt.append(R1_enc_sum_stmt0 & reduce(lambda x, y: x & y, R1_range_stmt0[:])) 

    R1_enc_stmt = reduce(lambda x, y: x | y, R1_enc_stmt) 

    #PROOF OF ENCRYPTION   ct_lv = Enc(pk_vs, lv, r_lv) 
    R1_enc_stmt2 = DLRep(ct_lv[0], r_lv*g) & DLRep(ct_lv[1], lv*g + r_lv*pk_vs)

    #PROOF OF RE-ENCRYPTION ct_lid = ReEnc(pk_vs, g*ct_i, r_lid)
    R1_reenc_stmt = DLRep(ct_lid[0], one*ct_i[0] + r_lid*g) & DLRep(ct_lid[1], one*(ct_i[1]+g) + r_lid*pk_vs)

    #PROOF OF KNOWLEDGE upk_id=g*sk_id
    R1_know_stmt = DLRep(upk, sk_id * g)

    #RELATION 1 STATEMENT
    R1_stmt1 = R1_enc_stmt  & R1_enc_stmt2 & R1_reenc_stmt & R1_know_stmt 

    #----------
    #RELATION 2 
    #----------

    #FIRST PROOF OF RE-ENCRYPTION ct_v = ReEnc(pk_T, ct_v-1, r_v)
    R2_reenc_stmt1 = [0]*candidates
    for i in range(candidates):
        R2_reenc_stmt1[i] = DLRep(ct_v[i][0], one*ct_bar_v[i][0] + r_v*g) & DLRep(ct_v[i][1], one*ct_bar_v[i][1] + r_v*pk_T)
    R2_result_stmt1 = reduce(lambda x, y: x & y, R2_reenc_stmt1)

    #SECOND PROOF OF RE-ENCRYPTION ct_lv = ReEnc(pk_vs, ct_i, r_lv)
    R2_reenc_stmt2 = DLRep(ct_lv[0], one*ct_i[0] + r_lv*g) & DLRep(ct_lv[1], one*ct_i[1] + r_lv*pk_vs)

    #THIRD PROOF OF RE-ENCRYPTION ct_lid = ReEnc(pk_vs, ct_i, r_lid)
    R2_reenc_stmt3 = DLRep(ct_lid[0], one*ct_i[0] + r_lid*g) & DLRep(ct_lid[1], one*ct_i[1] + r_lid*pk_vs)

    #PROOF OF DECRYPTION   1 = Dec(sk_id, (ct_lv-1)-(ct_lid-1))
    R2_dec_stmt = DLRep(0*g, one*c1 + sk_vs*neg_c0)

    #RELATION 2 STATEMENT
    R2_stmt = R2_dec_stmt & R2_result_stmt1  &  R2_reenc_stmt2 & R2_reenc_stmt3

    
    #----------
    #RELATION 3 
    #----------

    #FIRST PROOF OF RE-ENCRYPTION ct_v = ReEnc(pk_T, ct_v-2, r_v)
    R3_reenc_stmt1 = [0]*candidates
    for i in range(candidates):
        R3_reenc_stmt1[i] = DLRep(ct_v[i][0], one*ct_bar_vv[i][0] + r_v*g) & DLRep(ct_v[i][1], one*ct_bar_vv[i][1] + r_v*pk_T)
    R3_result_stmt1 = reduce(lambda x, y: x & y, R3_reenc_stmt1)

    #SECOND PROOF OF RE-ENCRYPTION ct_lv = ReEnc(pk_vs, ct_i, r_lv)
    R3_reenc_stmt2 = DLRep(ct_lv[0], one*ct_i[0] + r_lv*g) & DLRep(ct_lv[1], one*ct_i[1] + r_lv*pk_vs)

    #THIRD PROOF OF RE-ENCRYPTION ct_lid = ReEnc(pk_vs, ct_i, r_lid)
    R3_reenc_stmt3 = DLRep(ct_lid[0], one*ct_i[0] + r_lid*g) & DLRep(ct_lid[1], one*ct_i[1] + r_lid*pk_vs)

    #PROOF OF DL INEQUALITY    1 <> Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) 
    R3_dec_stmt = DLNotEqual([pk_vs,g],[c1,c0],sk_vs)
  
    #RELATION 3 STATEMENT
    R3_stmt =  R3_dec_stmt & R3_result_stmt1 & R3_reenc_stmt2 & R3_reenc_stmt3

    return R1_stmt1 | R2_stmt | R3_stmt