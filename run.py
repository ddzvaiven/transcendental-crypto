#!/usr/bin/env python
"""
Launcher script for transcendental cryptography CLI.
This avoids the runtime warning by properly importing the main function.
"""
from cli.main import main

if __name__ == "__main__":
    main()
