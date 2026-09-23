"""Manually verify a configured ResilientDB key-value service."""

from backend.storage.kv import get_kv, set_kv


def main():
    print("Testing KV service with same key...")
    result = set_kv("test", "hello world")
    print(f"Set result: {result}")
    value = get_kv("test")
    print(f'Get result: "{value}"')


if __name__ == "__main__":
    main()
