import json
import os

# Always resolve relative to the project root
CONSTANTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/constants.json'))

with open(CONSTANTS_PATH, 'r') as f:
    CONSTANTS = json.load(f) 