import random
from typing import List, Tuple, Optional
import base64
from math import ceil
import secrets
from decimal import Decimal, getcontext

class ShamirSecretSharing:
    def __init__(self):
        """Initialize the secret sharing system"""
        self.PRIME = 2**521 - 1  # Mersenne prime
        self.internal_key_size = 256  # Size used for shares
        self.aes_key_size = 32      # Size needed for AES-256
        getcontext().prec = 1024    # High precision for calculations

    def _eval_polynomial(self, coefficients: List[int], x: int, prime: int) -> int:
        """Evaluate polynomial at point x"""
        y = 0
        for coefficient in reversed(coefficients):
            y = (y * x + coefficient) % prime
        return y

    def _mod_inverse(self, a: int, m: int) -> int:
        """Calculate modular multiplicative inverse"""
        def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
            if a == 0:
                return b, 0, 1
            gcd, x1, y1 = extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y

        _, x, _ = extended_gcd(a, m)
        return (x % m + m) % m

    def _lagrange_interpolate(self, points: List[Tuple[int, int]], prime: int) -> int:
        """Lagrange interpolation to reconstruct the secret"""
        result = 0
        for i, (xi, yi) in enumerate(points):
            numerator = denominator = 1
            for j, (xj, _) in enumerate(points):
                if i != j:
                    numerator = (numerator * (-xj)) % prime
                    denominator = (denominator * (xi - xj)) % prime
            lagrange_basis = (numerator * self._mod_inverse(denominator, prime)) % prime
            result = (result + yi * lagrange_basis) % prime
        return result

    def split_secret(self, secret: bytes, n: int, k: int) -> List[Tuple[int, bytes]]:
        """
        Split a secret into n shares using Shamir's Secret Sharing
        k shares are required to reconstruct (k <= n)
        Returns: List of (index, share) tuples
        """
        if k > n:
            raise ValueError("Threshold k cannot be greater than total shares n")
        
        if len(secret) != self.aes_key_size:
            raise ValueError(f"Secret must be exactly {self.aes_key_size} bytes for AES-256")
        
        # Convert secret to integer
        secret_int = int.from_bytes(secret, 'big')
        if secret_int >= self.PRIME:
            raise ValueError("Secret is too large for the chosen prime")
        
        # Generate random coefficients for polynomial
        coefficients = [secret_int] + [secrets.randbelow(self.PRIME) for _ in range(k-1)]
        
        # Generate shares
        shares = []
        for i in range(1, n+1):
            # Evaluate polynomial
            share_value = self._eval_polynomial(coefficients, i, self.PRIME)
            # Convert to bytes with fixed length
            share_bytes = share_value.to_bytes(ceil(self.PRIME.bit_length() / 8), 'big')
            shares.append((i, share_bytes))
        
        return shares

    def reconstruct_secret(self, shares: List[Tuple[int, bytes]], original_secret_size: int) -> Optional[bytes]:
        """
        Reconstruct the secret from k or more shares using Lagrange interpolation
        Returns: The reconstructed secret
        """
        if not shares:
            print("No shares provided")
            return None
            
        try:
            # Convert shares back to integers
            points = [(x, int.from_bytes(share, 'big')) for x, share in shares]
            
            # Perform Lagrange interpolation
            secret_int = self._lagrange_interpolate(points, self.PRIME)
            
            # Convert back to bytes
            reconstructed_secret = secret_int.to_bytes(self.aes_key_size, 'big')
            print(f"Successfully reconstructed {len(reconstructed_secret)} bytes for AES key")
            return reconstructed_secret
            
        except Exception as e:
            print(f"Error during secret reconstruction: {e}")
            return None

    def encode_share(self, share: Tuple[int, bytes]) -> str:
        """
        Encode a share to a string format
        Format: <index>:<base64_encoded_share>
        """
        x, share_bytes = share
        return f"{x}:{base64.b64encode(share_bytes).decode()}"

    def decode_share(self, encoded_share: str) -> Tuple[int, bytes]:
        """
        Decode a share from string format
        Format: <index>:<base64_encoded_share>
        """
        try:
            x_str, b64_share = encoded_share.split(":")
            x = int(x_str)
            share_bytes = base64.b64decode(b64_share)
            return (x, share_bytes)
        except Exception as e:
            print(f"Error decoding share: {e}")
            raise
