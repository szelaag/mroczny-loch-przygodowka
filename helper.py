import os

def clear_system():
    os.system('cls' if os.name == 'nt' else 'clear')