import importlib.resources as pkg_resources
from eth_account.signers.base import BaseAccount
from web3 import Web3
from web3.contract import Contract
from eth_typing import HexStr
import json
from .. import contract_abi

l2_eth_bridge_abi_cache = None


def _l2_eth_bridge_abi_default():
    global l2_eth_bridge_abi_cache

    if l2_eth_bridge_abi_cache is None:
        with pkg_resources.path(contract_abi, "L2ETHBridge.json") as p:
            with p.open(mode='r') as json_file:
                data = json.load(json_file)
                l2_eth_bridge_abi_cache = data['abi']
    return l2_eth_bridge_abi_cache


class L2ETHBridge:

    def __init__(self, contract_address: HexStr, web3: Web3, zksync_account: BaseAccount, abi=None):
        check_sum_address = Web3.toChecksumAddress(contract_address)
        self.web3 = web3
        self.addr = check_sum_address
        self.zksync_account = zksync_account
        if abi is None:
            abi = _l2_eth_bridge_abi_default()
        self._contract: Contract = self.web3.eth.contract(self.addr, abi=abi)

    def _get_nonce(self):
        return self.web3.zksync.get_transaction_count(self.zksync_account.address)

    def balance_of(self, addr: HexStr):
        return self._contract.functions.balanceOf(addr).call()

    def finalize_deposit(self,
                         l1_sender: HexStr,
                         l2_receiver: HexStr,
                         l1_token: HexStr,
                         amount: int,
                         data: bytes):
        tx = self._contract.functions.finalizeDeposit(l1_sender,
                                                      l2_receiver,
                                                      l1_token,
                                                      amount,
                                                      data).build_transaction(
            {
                "from": self.zksync_account.address,
                "nonce": self._get_nonce()
            })
        signed_tx = self.zksync_account.sign_transaction(tx)
        txn_hash = self.web3.zksync.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.zksync.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    def l1_bridge(self):
        return self._contract.functions.l1Bridge().call()

    def l1_token_address(self, addr: HexStr):
        return self._contract.functions.l1TokenAddress(addr).call()

    def l2_token_address(self, l1_token: HexStr):
        return self._contract.functions.l2TokenAddress(l1_token).call()

    def total_supply(self):
        return self._contract.functions.totalSupply().call()

    def withdraw(self,
                 l1_receiver: HexStr,
                 l2_token: HexStr,
                 amount: int):
        tx = self._contract.functions.withdraw(l1_receiver,
                                               l2_token,
                                               amount).build_transaction(
            {
                "from": self.zksync_account.address,
                "nonce": self._get_nonce()
            })
        signed_tx = self.zksync_account.sign_transaction(tx)
        txn_hash = self.web3.zksync.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.zksync.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    @property
    def contract(self):
        return self._contract

    @property
    def address(self):
        return self.addr