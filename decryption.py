from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import hashlib

def decrypt_symmetric(ciphertext_blob, passphrase):
    """Decrypts data using a symmetric passphrase (AES-GCM)."""
    if len(ciphertext_blob) < 28:
        raise ValueError("Ciphertext blob is too short.")

    salt = ciphertext_blob[:16]
    key = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 600000, dklen=32)
    
    aesgcm = AESGCM(key)
    nonce = ciphertext_blob[16:28]
    ciphertext = ciphertext_blob[28:]
    
    return aesgcm.decrypt(nonce, ciphertext, None)

def decrypt_asymmetric(ciphertext_blob, private_key_text):
    """
    Decrypts data using a hybrid RSA approach.
    Bundle format: [Len of Encrypted Key (4 bytes)] + [Encrypted Key] + [Nonce (12 bytes)] + [Ciphertext]
    """
    # Load the RSA private key from PEM format
    private_key = serialization.load_pem_private_key(
        private_key_text.encode(),
        password=None
    )
    
    # 1. Extract the encrypted session key
    key_len = int.from_bytes(ciphertext_blob[:4], byteorder='big')
    encrypted_session_key = ciphertext_blob[4 : 4 + key_len]
    
    # 2. Decrypt the session key with the RSA Private Key
    session_key = private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # 3. Decrypt the actual data with the session key
    nonce = ciphertext_blob[4 + key_len : 4 + key_len + 12]
    ciphertext = ciphertext_blob[4 + key_len + 12 :]
    
    aesgcm = AESGCM(session_key)
    return aesgcm.decrypt(nonce, ciphertext, None)

def decrypt_file(ciphertext_blob, passphrase=None, private_key=None):
    """
    Decrypts a binary blob and returns the plaintext.
    """
    if private_key:
        return decrypt_asymmetric(ciphertext_blob, private_key)
    elif passphrase:
        return decrypt_symmetric(ciphertext_blob, passphrase)
    else:
        raise ValueError("Either a passphrase or a private key must be provided.")
