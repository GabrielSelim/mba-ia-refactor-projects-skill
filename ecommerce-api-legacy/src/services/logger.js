// Logger mínimo com níveis (sem dependência nova). Nunca registre senha, cartão ou chave.
const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
  const threshold = LEVELS[level] ?? LEVELS.info;
  const emit = (lvl, method) => (message, meta) => {
    if (LEVELS[lvl] > threshold) return;
    const line = `${new Date().toISOString()} ${lvl.toUpperCase()} ${message}`;
    method(meta === undefined ? line : `${line} ${JSON.stringify(meta)}`);
  };
  return {
    error: emit('error', console.error),
    warn: emit('warn', console.warn),
    info: emit('info', console.log),
    debug: emit('debug', console.log),
  };
}

module.exports = { createLogger };
