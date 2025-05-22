"""
A script to generate digit files for π and e for transcendental cryptography.

This script generates reliable digit files that can be included in the repository.
"""
import mpmath
import os

def generate_pi_digits(digits=1000000, output_file="pi_1m.txt"):
    """Generate π digits and save to a file."""
    print(f"Generating {digits} digits of π...")
    
    # Set precision to ensure accurate computation
    mpmath.mp.dps = digits + 10
    
    # Generate π with specified precision
    pi = mpmath.mp.pi
    
    # Convert to string and save
    pi_str = str(pi)
    
    with open(output_file, 'w') as f:
        f.write(pi_str)
    
    print(f"Saved {len(pi_str)} digits of π to {output_file}")

def generate_e_digits(digits=1000000, output_file="e_1m.txt"):
    """Generate e digits and save to a file."""
    print(f"Generating {digits} digits of e...")
    
    # Set precision to ensure accurate computation
    mpmath.mp.dps = digits + 10
    
    # Generate e with specified precision
    e = mpmath.mp.e
    
    # Convert to string and save
    e_str = str(e)
    
    with open(output_file, 'w') as f:
        f.write(e_str)
    
    print(f"Saved {len(e_str)} digits of e to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate digit files for π and e")
    parser.add_argument("--digits", type=int, default=1000000, help="Number of digits to generate")
    parser.add_argument("--pi-output", type=str, default="pi_1m.txt", help="Output file for π digits")
    parser.add_argument("--e-output", type=str, default="e_1m.txt", help="Output file for e digits")
    parser.add_argument("--directory", type=str, default="data", help="Directory to save files in")
    
    args = parser.parse_args()
    
    # Ensure directory exists
    os.makedirs(args.directory, exist_ok=True)
    
    # Generate digits
    generate_pi_digits(args.digits, os.path.join(args.directory, args.pi_output))
    generate_e_digits(args.digits, os.path.join(args.directory, args.e_output))
