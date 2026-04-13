import json
import hashlib
import os
from datetime import datetime

CHAIN_FILE = "logs/blockchain_chain.json"


def calculate_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()


def load_chain():
    if not os.path.exists(CHAIN_FILE):
        return []

    try:
        with open(CHAIN_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_chain(chain):
    os.makedirs("logs", exist_ok=True)
    with open(CHAIN_FILE, "w") as f:
        json.dump(chain, f, indent=2)


def add_block(block_type, message, extra=None):

    chain = load_chain()

    prev_hash = chain[-1]["hash"] if chain else "000000"

    block_data = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": block_type,
        "msg": message,
        "extra": extra,
        "prev": prev_hash
    }

    block_string = json.dumps(block_data, sort_keys=True)
    block_hash = calculate_hash(block_string)

    block_data["hash"] = block_hash

    chain.append(block_data)

    save_chain(chain)