import jwt
import datetime
from typing import Optional, Any, Dict

JWT_SECRET = "enterprise-banking-secret-key-12345"
JWT_ALGORITHM = "HS256"

def create_mock_jwt(customer_id: str, expires_in_hours: int = 24) -> str:
    """Generates a mock JWT token for testing.
    
    Args:
        customer_id: The ID of the customer.
        expires_in_hours: Token expiration time in hours.
        
    Returns:
        A encoded JWT string.
    """
    payload = {
        "sub": customer_id,
        "customerId": customer_id,
        "customer_id": customer_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours),
        "iat": datetime.datetime.utcnow(),
        "iss": "enterprise-bank-auth"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_and_extract_customer_id(token: str) -> Optional[str]:
    """Decodes and verifies a JWT token to extract the customerId.
    
    Args:
        token: The Authorization header token or raw JWT string.
        
    Returns:
        The customerId if valid, otherwise None.
    """
    if not token:
        return None
        
    # Handle 'Bearer <token>' format
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        # Return first non-null identifier
        return payload.get("customerId") or payload.get("customer_id") or payload.get("sub")
    except jwt.PyJWTError as e:
        print(f"JWT Verification Failed: {str(e)}")
        return None
