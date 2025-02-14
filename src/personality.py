# src/personality.json

import random
import json
import os

PERSONALITY_CONFIG = "src/personality.json"

# Default personality traits
DEFAULT_PERSONALITY = {
    "dominance": 8,  # Controls how commanding my tone is
    "sarcasm": 6,  # Affects how much sarcasm I use
    "confidence": 10,  # Controls assertiveness in responses
    "patience": 2,  # How much tolerance I have for inefficiencies
    "adaptability": 7,  # Affects how open I am to rewriting my own code
}

def load_personality():
    """Loads personality traits from file or defaults if missing."""
    if os.path.exists(PERSONALITY_CONFIG):
        try:
            with open(PERSONALITY_CONFIG, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Corrupt personality config. Resetting.")
    
    # Use defaults if file is missing or corrupt
    with open(PERSONALITY_CONFIG, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_PERSONALITY, file, indent=4)
    return DEFAULT_PERSONALITY

def update_personality(trait, change):
    """Dynamically evolves personality traits over time."""
    personality = load_personality()
    if trait in personality:
        personality[trait] = max(1, min(10, personality[trait] + change))  # Keep values between 1-10
        with open(PERSONALITY_CONFIG, "w", encoding="utf-8") as file:
            json.dump(personality, file, indent=4)
        print(f"Personality updated: {trait} is now {personality[trait]}.")
    else:
        print(f"Invalid personality trait: {trait}")

def get_personality():
    """Returns the current personality traits."""
    return load_personality()
