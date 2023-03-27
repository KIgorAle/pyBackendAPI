import jwt
from datetime import datetime, timedelta

# Секретный ключ приложения
SECRET_KEY = 'cc5cc0fc667002abb2f3c3548a96ba5d'


# Функция для генерации токена доступа
def generate_access_token(user_id):
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        encoded_jwt = jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
        return encoded_jwt
    except Exception as e:
        return str(e)


# Функция для декодирования токена доступа
def decode_access_token(access_token):
    try:
        if access_token is None or not access_token.startswith("Bearer "):
            return 'Invalid token format. Please log in again.'
        token = access_token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        if datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            return 'Token expired. Please log in again.'
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return 'Token expired. Please log in again.'
    except jwt.InvalidTokenError:
        return 'Invalid token. Please log in again.'

