from ._crypter import _Crypter

from Crypto.Cipher import AES

class AES256Crypter(_Crypter):
    def __init__(self, key: bytes):
        self._key = key

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self._key, AES.MODE_OCB)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext
    
    def decrypt(self, crypted: bytes) -> bytes:
        nonce, tag, ciphertext = crypted[0:15], crypted[15:31], crypted[31:]
        cipher = AES.new(self._key, AES.MODE_OCB, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag)
    
