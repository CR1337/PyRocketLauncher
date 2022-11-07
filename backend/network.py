import os


def get_gateway_ip() -> str:
    return os.environ['GATEWAY_IP']
