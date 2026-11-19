"""Password hashing and session-token helpers (NFR-USR-01)."""

import base64
import hashlib
import hmac
import secrets

import bcrypt


class PasswordHasher:
    """Salted bcrypt hashes. The password is pre-hashed so length never matters."""

    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds
        self._dummy_hash: bytes | None = None

    @staticmethod
    def _prepare(password: str) -> bytes:
        return base64.b64encode(hashlib.sha256(password.encode()).digest())

    def hash(self, password: str) -> str:
        """Return a salted bcrypt hash of the password."""
        return bcrypt.hashpw(self._prepare(password), bcrypt.gensalt(self.rounds)).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        """Check a password against a stored hash."""
        return bcrypt.checkpw(self._prepare(password), password_hash.encode())

    def verify_dummy(self, password: str) -> None:
        """Spend the same time as a real check, so unknown emails are not detectable."""
        if self._dummy_hash is None:
            self._dummy_hash = self.hash("dummy-password-1").encode()
        bcrypt.checkpw(self._prepare(password), self._dummy_hash)


class TokenService:
    """Creates opaque session tokens and the keyed hash stored in the database."""

    def __init__(self, secret_key: str) -> None:
        self._key = secret_key.encode()

    @staticmethod
    def new_token() -> str:
        """Return a fresh random token to hand to the client."""
        return secrets.token_urlsafe(32)

    def digest(self, token: str) -> str:
        """Return the value stored in place of the token."""
        return hmac.new(self._key, token.encode(), hashlib.sha256).hexdigest()
