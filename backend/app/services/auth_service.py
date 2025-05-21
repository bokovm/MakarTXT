# backend/app/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from flask import current_app
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    DecodeError
)

class AuthException(Exception):
    """Базовое исключение для ошибок аутентификации"""
    pass

class InvalidTokenException(AuthException):
    """Некорректный токен"""
    pass

class ExpiredTokenException(AuthException):
    """Истекший токен"""
    pass

def create_token(user_id: int, username: str) -> str:
    """
    Создает JWT токен для пользователя
    :param user_id: ID пользователя в системе
    :param username: Имя пользователя
    :return: Подписанный JWT токен
    """
    try:
        payload = {
            'sub': user_id,
            'username': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(
                hours=current_app.config.get('JWT_EXP_HOURS', 24)
            )
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    except Exception as e:
        current_app.logger.error(f"Ошибка генерации токена: {str(e)}")
        raise AuthException("Ошибка создания токена") from e

def validate_token(token: str) -> dict:
    """
    Валидирует JWT токен и возвращает payload
    :param token: JWT токен для проверки
    :return: Расшифрованный payload
    :raises InvalidTokenException: Если токен недействителен
    :raises ExpiredTokenException: Если токен истек
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except ExpiredSignatureError as e:
        current_app.logger.warning(f"Истекший токен: {str(e)}")
        raise ExpiredTokenException("Срок действия токена истек") from e
    except (InvalidTokenError, DecodeError) as e:
        current_app.logger.error(f"Некорректный токен: {str(e)}")
        raise InvalidTokenException("Недействительный токен") from e
    except Exception as e:
        current_app.logger.error(f"Ошибка валидации токена: {str(e)}")
        raise AuthException("Ошибка проверки токена") from e

def get_current_user(token: str) -> dict:
    """
    Возвращает информацию о текущем пользователе
    :param token: JWT токен
    :return: Информация о пользователе
    """
    try:
        payload = validate_token(token)
        return {
            'id': payload['sub'],
            'username': payload['username']
        }
    except AuthException as e:
        raise e
    except KeyError as e:
        current_app.logger.error(f"Неполный payload: {str(e)}")
        raise InvalidTokenException("Неполные данные в токене") from e