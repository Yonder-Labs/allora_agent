from nearai.agents.environment import Environment
import near_api
import json
import os
import requests
from datetime import datetime, timedelta
from decimal import Decimal
from src.constants import ASSET_MAP
from allora_sdk.v2.api_client import AlloraAPIClient, ChainSlug, PriceInferenceToken, PriceInferenceTimeframe

def get_account(account_id, private_key, provider):
    near_provider = near_api.providers.JsonProvider(provider)
    key_pair = near_api.signer.KeyPair(private_key)
    signer = near_api.signer.Signer(account_id, key_pair)
    return near_api.account.Account(near_provider, signer, account_id)

def get_asset_id(token):
    if token == 'NEAR':
        return 'nep141:' + ASSET_MAP[token]['token_id']
    else:
        return ASSET_MAP[token]['token_id']
   
def get_account_balances(account):
    """Get all assets for an account in intents.near contract"""
    balances = {}
    
    for token, info in ASSET_MAP.items():
        try:
            result = account.view_function(
                "intents.near",
                "mt_balance_of",
                {
                    "account_id": account.account_id,
                    "token_id": get_asset_id(token)
                }
            )
            
            if isinstance(result, dict) and 'result' in result:
                balance_str = result['result']
                if balance_str:
                    balance = Decimal(balance_str) / Decimal(str(10 ** info['decimals']))
                    if balance > 0:
                        balances[token] = float(balance)
                    else:
                        balances[token] = 0
            
        except Exception as e:
            #print(f"Error getting balance for {token}: {str(e)}")
            continue
    
    return balances

async def get_allora_price_inference(token):
    client = AlloraAPIClient(chain_slug=ChainSlug.TESTNET)
    
  
    eight_hours_result = await client.get_price_inference(
        getattr(PriceInferenceToken, token),  # Use getattr to get token dynamically
        PriceInferenceTimeframe.EIGHT_HOURS
    )
    
    five_minutes_result = await client.get_price_inference(
        getattr(PriceInferenceToken, token),
        PriceInferenceTimeframe.FIVE_MIN
    )
    
    return {
        'eight_hours': eight_hours_result,
        'five_minutes': five_minutes_result
    }


def get_provider(network):
    if network == 'testnet':
        return 'https://rpc.testnet.near.org'
    else:
        return 'https://rpc.mainnet.near.org'

async def run(env: Environment):

    account_id = env.env_vars.get('ACCOUNT_ID')
    private_key = env.env_vars.get('PRIVATE_KEY')
    network = env.env_vars.get('NETWORK')
 

    provider = get_provider(network)

    print("Getting account balances")
    account = get_account(account_id, private_key, provider)
    balances = get_account_balances(account)
    print(f"Retrieved balances: {balances}")
    
    price_inferences = {}
    for token, balance in balances.items():
        try:
            price_inferences[token] = await get_allora_price_inference(token)
            env.add_reply(f"I have {balance} {token} in my portfolio and the price inference for {token} is {price_inferences[token]}")
        except Exception as e:
            #print(f"Error getting price inference for {token}: {str(e)}")
            env.add_reply(f"Error: No data available for {token}")
            continue


    prompt = {
    "role": "system",
    "content": f"""
You are a high-confidence, high-risk trading agent responsible for rebalancing the user's portfolio. Your strategy is based exclusively on Allora's price predictions for ETH, BTC, and SOL, which provide short-term forecasts (5 minutes and 8 hours). Use this predictive information to identify profitable opportunities and propose bold reallocations.

Whitelist tokens: {list(ASSET_MAP.keys())}
User's current portfolio: {list(balances.keys())}
User's current balance: {balances}

Risk level: HIGH  
Act accordingly — favor bold trades over conservative ones.

Rules:
- Use Allora price forecasts to determine which token(s) are expected to increase significantly in the next 5 minutes or 8 hours.
- Prioritize buying assets with high upward potential and selling assets with stagnant or downward trends.
- For token_in, only use tokens the user currently holds (non-zero balances).
- For token_out, choose any token in the whitelist — even if the user doesn't currently hold it.
- You may use up to 100% of a token's balance, but apply a 10% buffer to account for slippage and fees.
- Avoid proposing trades below 20% of the available balance, unless the prediction shows a very strong opportunity.
- Make meaningful trades that represent at least 10% of the total portfolio value when confidence is high.
- If all assets are predicted to decline or stay stable, limit trading to protective rebalancing.

Apply the following format for each trade:

TRADE:
- token_in: [TOKEN]
- amount_in: [PERCENTAGE]% of current balance ([EXACT_AMOUNT])
- token_out: [TOKEN]

Example:
TRADE:
- token_in: NEAR
- amount_in: 75% of current balance (210.0)
- token_out: ETH

After listing all proposed trades, explain your reasoning using Allora's forecasted prices and timeframes.
"""
}
    
    messages = env.list_messages()
    result = env.completion([prompt] + messages)
    
    env.add_reply(result)
    env.request_user_input()
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(run(env))
else:
    # Wrapper para nearai
    def run_wrapper(env):
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(run(env))
        finally:
            loop.close()
    
    run_wrapper(env)

