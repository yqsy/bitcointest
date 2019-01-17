from bitcoin.core import *
from bitcoin.core.script import *
from bitcoin.wallet import *

import bitcoin


def main():
    bitcoin.SelectParams('mainnet')

    # 发送者私钥 & P2PK锁定脚本
    senderSeckey = CBitcoinSecret('L2XxuM4B7GiVFwWhtriLugfWxMAB8AAn63dpygovyczESzBK6p4o')
    senderP2PKScriptPubkey = CScript([senderSeckey.pub, OP_CHECKSIG])

    # 接收者私钥 & 地址 & P2PKH锁定脚本
    receiverSeckey = CBitcoinSecret('KxbMqfhaN8NFXPCmHE4ZupJfBYRDj46iT1YxNqHrJcrpmaKMiL6C')
    receiverP2PKHAddr = P2PKHBitcoinAddress.from_pubkey(receiverSeckey.pub)
    receiverP2PKHScriptPubKey = receiverP2PKHAddr.to_scriptPubKey()

    # [height] checklocktimeverify pubkey checksig
    redeemScript = CScript(
        [300, OP_CHECKLOCKTIMEVERIFY, OP_DROP] + list(senderP2PKScriptPubkey), )

    # p2sh 的锁定脚本
    p2shScriptPubkey = redeemScript.to_p2sh_scriptPubKey()

    # p2sh 地址
    p2shAddr = CBitcoinAddress.from_scriptPubKey(p2shScriptPubkey)

    print("redeemScript: {}".format(redeemScript.hex()))
    print("p2shAddr: {}".format(p2shAddr))

    preOutPut = COutPoint(lx('074a7c0f3a232849276688a9a232e32873ba6eca6c6bd30bd95d15283ce30e21'), 0)

    unsignedTx = CTransaction(
        [CTxIn(preOutPut, CScript(), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), receiverP2PKHScriptPubKey)],
        nLockTime=300,
        nVersion=1)

    sighash = SignatureHash(redeemScript, unsignedTx, 0, SIGHASH_ALL)

    sig = senderSeckey.sign(sighash) + bytes([SIGHASH_ALL])

    signedTx = CTransaction(
        [CTxIn(preOutPut, CScript([sig, redeemScript]), nSequence=1 << 31)],
        [CTxOut(int(49.9999 * COIN), receiverP2PKHScriptPubKey)],
        nLockTime=300,
        nVersion=1)

    print("signedTx: {}".format(signedTx.serialize().hex()))


if __name__ == "__main__":
    main()
