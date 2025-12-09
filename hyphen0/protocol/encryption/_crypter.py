class _Crypter:
    def encrypt(self, data: bytes) -> bytes:
        raise NotImplementedError("tried to use raw _Crypter")
    
    def decrypt(self, crypted: bytes) -> bytes:
        raise NotImplementedError("tried to use raw _Crypter")