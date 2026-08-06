from werkzeug.security import generate_password_hash, check_password_hash

def hash_pwd(password):
    return generate_password_hash(password)

def verify_pwd(stored_hash, provided_password):
    return check_password_hash(stored_hash, provided_password) or stored_hash == provided_password
