from backend.auth.security import hash_password, verify_password

h = hash_password("123456")
print(verify_password("123456", h))  # True
