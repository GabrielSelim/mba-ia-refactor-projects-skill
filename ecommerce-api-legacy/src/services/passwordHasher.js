// Hash de senha com scrypt + salt aleatório (crypto nativo do Node), no lugar do antigo badCrypto.
const crypto = require('crypto');

const KEY_LENGTH = 64;

function createPasswordHasher() {
  return {
    hash(password) {
      const salt = crypto.randomBytes(16).toString('hex');
      const derived = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
      return `${salt}:${derived}`;
    },
    verify(password, stored) {
      const [salt, expected] = String(stored).split(':');
      if (!salt || !expected) return false;
      const derived = crypto.scryptSync(password, salt, KEY_LENGTH);
      const expectedBuf = Buffer.from(expected, 'hex');
      return expectedBuf.length === derived.length && crypto.timingSafeEqual(derived, expectedBuf);
    },
  };
}

module.exports = { createPasswordHasher };
