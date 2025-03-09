import os
from mt5linux import MetaTrader5

def connect_to_mt5():
    mt5 = MetaTrader5('mt5app',8001)
    mt5.initialize()
    
    print(mt5.terminal_info()._asdict())
    print(mt5.version())


def main():
    connect_to_mt5()
    
if __name__ == "__main__":
    print("hello")
    print("Starting MT5 connection test...")
    # Run once immediately
    main()

