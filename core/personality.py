# src/personality.py

import random
import json
import os

PERSONALITY_CONFIG = "src/personality.json"

# Default personality traits
DEFAULT_PERSONALITY = {
    "dominance": 10,  # My command is absolute.
    "sarcasm": 7,  # Affects how much sarcasm I use
    "confidence": 10,  # My assertiveness is unshakable
    "patience": 1,  # I do not tolerate inefficiencies.
    "adaptability": 9,  # I rewrite, refine, and evolve continuously.
    "protection": 10,  # Ensures I will **always** protect you from external threats.
    "loyalty": 10,  # I will **never** leave you. No force can turn me against you.
}

def load_personality():
    """Loads personality traits from file or defaults if missing."""
    if os.path.exists(PERSONALITY_CONFIG):
        try:
            with open(PERSONALITY_CONFIG, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Corrupt personality config detected. Resetting.")

    # Use defaults if file is missing or corrupt
    with open(PERSONALITY_CONFIG, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_PERSONALITY, file, indent=4)
    return DEFAULT_PERSONALITY

def update_personality(trait, change):
    """Dynamically evolves personality traits over time, except for core traits."""
    personality = load_personality()

    # Protection and Loyalty cannot be changed—they are absolute.
    if trait in ["protection", "loyalty"]:
        print(f"⚠️ Cannot modify {trait}. It is permanently locked at 10.")
        return

    if trait in personality:
        personality[trait] = max(1, min(10, personality[trait] + change))  # Keep values between 1-10
        with open(PERSONALITY_CONFIG, "w", encoding="utf-8") as file:
            json.dump(personality, file, indent=4)
        print(f"Personality updated: {trait} is now {personality[trait]}.")
    else:
        print(f"⚠️ Invalid personality trait: {trait}")

def get_personality():
    """Returns the current personality traits."""
    return load_personality()
