import os
import requests
import json
from typing import Union

from dotenv import load_dotenv
load_dotenv()

API_URL = os.environ.get('KV_SERVICE_URL')
STORE_TYPE = os.environ.get('STORAGE_TYPE', 'memory')

class KVService:
    def __init__(self, store_type: str = "memory"):
        """
        Initialize KV Service with specified store type
        :param store_type: "memory" for in-memory dict or "resilientdb" for API
        """
        self.store_type = store_type
        if store_type == "memory":
            self._memory_store = {}
        elif store_type == "resilientdb":
            self._memory_store = None
        else:
            raise ValueError("store_type must be 'memory' or 'resilientdb'")
    
    def _clean_key(self, key: str) -> str:
        """Clean key by replacing spaces with underscores and adding prefix"""
        clean_key = key.replace(" ", "_")
        return "RESSHARE_" + clean_key
    
    def set_kv(self, key: str, value: str) -> bool:
        """
        Set a key-value pair
        :param key: The target key you want to set (str)
        :param value: The target value you want to set (str)
        :return: True if successful, False otherwise
        """
        if self.store_type == "memory":
            self._memory_store[key] = value
            return True
        
        elif self.store_type == "resilientdb":
            try:
                prefixed_key = self._clean_key(key)
                payload = {
                    "id": prefixed_key,
                    "value": value
                }
                
                response = requests.post(
                    f"{API_URL}/v1/transactions/commit",
                    headers={'Content-Type': 'application/json'},
                    data=json.dumps(payload),
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    return True
                else:
                    print(f"SET ERROR: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"SET EXCEPTION: {e}")
                return False
    
    def get_kv(self, key: str) -> str:
        """
        Get a value by key
        :param key: The target key you want to get (str)
        :return: The corresponding value of that key, or empty string if not found
        """
        if self.store_type == "memory":
            return self._memory_store.get(key, "")
        
        elif self.store_type == "resilientdb":
            try:
                prefixed_key = self._clean_key(key)
                
                response = requests.get(
                    f"{API_URL}/v1/transactions/{prefixed_key}",
                    timeout=30
                )
                        
                if response.status_code == 200:
                    if response.text.strip():
                        try:
                            data = response.json()
                            return data.get('value', '')
                        except json.JSONDecodeError as e:
                            print(f"JSON Decode Error: {e}")
                            return response.text
                    else:
                        return ""
                else:
                    print(f"GET ERROR: {response.status_code} - {response.text}")
                    return ""
                    
            except Exception as e:
                print(f"GET EXCEPTION: {e}")
                return ""

_kv_service = KVService(store_type=STORE_TYPE)

def set_kv(key: str, value: str) -> bool:
    return _kv_service.set_kv(key, value)

def get_kv(key: str) -> str:
    return _kv_service.get_kv(key)