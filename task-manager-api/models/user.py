import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import ROLE_ADMIN, utc_now

_LEGACY_MD5 = re.compile(r"^[0-9a-f]{32}$")


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        # O hash da senha nunca é serializado.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        """Verifica a senha; hashes MD5 legados são aceitos uma vez e migrados para o hash atual."""
        if _LEGACY_MD5.match(self.password or ""):
            legacy = hashlib.md5(raw_password.encode()).hexdigest()
            if hmac.compare_digest(legacy, self.password):
                self.set_password(raw_password)
                return True
            return False
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN
