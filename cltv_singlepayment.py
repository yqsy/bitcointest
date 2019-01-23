from bitcoin.core import *
from bitcoin.core.script import *
from bitcoin.wallet import *

import bitcoin

def main():
    bitcoin.SelectParams('mainnet')

    # 用户私钥 & 用户P2PK锁定脚本 & 地址 & P2PKH锁定脚本
    senderSeckey = CBitcoinSecret('L2XxuM4B7GiVFwWhtriLugfWxMAB8AAn63dpygovyczESzBK6p4o')
    senderP2PKScriptPubkey = CScript([senderSeckey.pub, OP_CHECKSIG])
    senderP2PKHAddr = P2PKHBitcoinAddress.from_pubkey(senderSeckey.pub)
    senderP2PKHScriptPubkey = senderP2PKHAddr.to_scriptPubKey()

    # 商家私钥 & P2PK (非终结) & 地址 & P2PKH锁定脚本
    receiverSeckey = CBitcoinSecret('KxbMqfhaN8NFXPCmHE4ZupJfBYRDj46iT1YxNqHrJcrpmaKMiL6C')
    receiverP2PKScriptPubkey = CScript([receiverSeckey.pub, OP_CHECKSIGVERIFY])
    receiverP2PKHAddr = P2PKHBitcoinAddress.from_pubkey(receiverSeckey.pub)
    receiverP2PKHScriptPubkey = receiverP2PKHAddr.to_scriptPubKey()

    # 1. 商家 & 用户 签名了可以见证
    # 2. 指定时间后 用户签名了可以见证
    # if
    #    servicePubkey checksigverify
    # else
    #    [height] checklocktimeverify drop
    # endif
    # userPubkey checksig

    redeemScript = CScript(
        [OP_IF] + \
            list(receiverP2PKScriptPubkey) + \
        [OP_ELSE,
            300,  OP_CHECKLOCKTIMEVERIFY, OP_DROP,
         OP_ENDIF] + \
            list(senderP2PKScriptPubkey),
    )

    # p2sh 的锁定脚本
    p2shScriptPubkey = redeemScript.to_p2sh_scriptPubKey()

    # p2sh 地址
    p2shAddr = CBitcoinAddress.from_scriptPubKey(p2shScriptPubkey)

    print("redeemScript: {}".format(redeemScript.hex()))
    print("p2shAddr: {}".format(p2shAddr))

    preOutPut = COutPoint(lx('79d7b818b6e1a99e2bbdb51263c3d552a25af19f35a1857faf174c0651e5243c'), 0)

    # 场景1: 超时后退还钱给用户
    sense1(preOutPut, redeemScript, senderP2PKHScriptPubkey, senderSeckey)

    # 场景2: 商家和用户一起签名把钱给商家
    sense2(preOutPut, receiverP2PKHScriptPubkey, receiverSeckey, redeemScript, senderSeckey)

    # 场景3: 用户和商家链下签名,最终商家链上结算
    sense3(preOutPut, receiverP2PKHScriptPubkey, receiverSeckey, redeemScript, senderP2PKHScriptPubkey, senderSeckey)


def sense3(preOutPut, receiverP2PKHScriptPubkey, receiverSeckey, redeemScript, senderP2PKHScriptPubkey, senderSeckey):
    # 用户存款 (手续费用为: 49.99996220 - 49.9999 = ), 在存款中忽视了6220
    senderFund = 49.9999 * COIN
    # 累计费用
    sumCost = 0
    # 锁定时间
    nLockTime = 300

    for i in range(0, 10):
        sumCost += 1.0 * COIN
        unsignedTx = CTransaction(
            [CTxIn(preOutPut, CScript(), nSequence=1 << 31)],
            [CTxOut(int(senderFund - sumCost), senderP2PKHScriptPubkey),  # 用户余额度
             CTxOut(int(sumCost), receiverP2PKHScriptPubkey)],  # 商家应得奖励
            nLockTime=nLockTime,
            nVersion=1)

        sighash = SignatureHash(redeemScript, unsignedTx, 0, SIGHASH_ALL)
        senderSig = senderSeckey.sign(sighash) + bytes([SIGHASH_ALL])

        # 用户将签名和交易给商家

        receiverSig = receiverSeckey.sign(sighash) + bytes([SIGHASH_ALL])

        # 商家提供服务, 并签名交易做结算用
        SignedTx = CTransaction(
            [CTxIn(preOutPut, CScript([senderSig, receiverSig, 1, redeemScript]), nSequence=1 << 31)],
            [CTxOut(int(senderFund - sumCost), senderP2PKHScriptPubkey),  # 用户余额度
             CTxOut(int(sumCost), receiverP2PKHScriptPubkey)],  # 商家应得奖励
            nLockTime=nLockTime,
            nVersion=1)

        print("scene 3: {}".format(SignedTx.serialize().hex()))
        nLockTime -= 1

def sense2(preOutPut, receiverP2PKHScriptPubkey, receiverSeckey, redeemScript, senderSeckey):
    unsignedTx = CTransaction(
        [CTxIn(preOutPut, CScript(), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), receiverP2PKHScriptPubkey)],
        nLockTime=0,
        nVersion=1)
    sighash = SignatureHash(redeemScript, unsignedTx, 0, SIGHASH_ALL)
    senderSig = senderSeckey.sign(sighash) + bytes([SIGHASH_ALL])
    receiverSig = receiverSeckey.sign(sighash) + bytes([SIGHASH_ALL])
    SignedTx = CTransaction(
        [CTxIn(preOutPut, CScript([senderSig, receiverSig, 1, redeemScript]), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), receiverP2PKHScriptPubkey)],
        nLockTime=0,
        nVersion=1)
    print("scene 2: {}".format(SignedTx.serialize().hex()))


def sense1(preOutPut, redeemScript, senderP2PKHScriptPubkey, senderSeckey):
    unsignedTx = CTransaction(
        [CTxIn(preOutPut, CScript(), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), senderP2PKHScriptPubkey)],
        nLockTime=300,
        nVersion=1)
    sighash = SignatureHash(redeemScript, unsignedTx, 0, SIGHASH_ALL)
    sig = senderSeckey.sign(sighash) + bytes([SIGHASH_ALL])
    signedTx = CTransaction(
        [CTxIn(preOutPut, CScript([sig, 0, redeemScript]), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), senderP2PKHScriptPubkey)],
        nLockTime=300,
        nVersion=1)
    print("scene 1: {}".format(signedTx.serialize().hex()))


if __name__ == "__main__":
    main()
