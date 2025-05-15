import os

# Path constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_PATH = os.path.join(BASE_DIR, "src", "agent")

# Asset mapping
ASSET_MAP = {
    'ETH': {
        'token_id': 'nep141:eth.omft.near',
        'decimals': 18,
        'blockchain': 'eth',
        'symbol': 'ETH',
        'price': 2079.16,
        'price_updated_at': "2025-03-25T15:11:40.065Z"
    },
    'BTC': {
        'token_id': 'nep141:btc.omft.near',
        'decimals': 8,
        'blockchain': 'btc',
        'symbol': 'BTC',
        'price': 88178,
        'price_updated_at': "2025-03-25T15:11:40.065Z"
    },
    'SOL': {    
        'token_id': 'nep141:sol.omft.near',
        'decimals': 9,
        'blockchain': 'sol',
        'symbol': 'SOL',
        'price': 146.28,
        'price_updated_at': "2025-03-25T15:11:40.065Z"
    }
} 