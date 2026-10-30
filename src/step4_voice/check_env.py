import os
from pathlib import Path
from dotenv import load_dotenv

def verify_env():
    env_path = Path(".env")
    print(f".env file exists: {env_path.exists()}")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        key = os.getenv("GNANI_API_KEY", "")
        print(f"GNANI_API_KEY detected: {bool(key)}")
        print(f"GNANI_API_KEY length: {len(key)}")
        print(f"GNANI_API_KEY prefix valid: {key.startswith('vach_')}")
    else:
        print(".env file NOT found!")

if __name__ == "__main__":
    verify_env()
