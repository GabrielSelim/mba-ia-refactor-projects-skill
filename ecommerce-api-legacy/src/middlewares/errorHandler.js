// Tratamento de erros centralizado: erros de domínio viram JSON; erros inesperados viram 500 genérico.
const { AppError } = require('../errors');

function createErrorHandler(logger) {
  // eslint-disable-next-line no-unused-vars
  return (err, req, res, next) => {
    if (err instanceof AppError) {
      return res.status(err.statusCode).json({ error: err.message });
    }
    if (err.type === 'entity.parse.failed') {
      return res.status(400).json({ error: 'Bad Request' });
    }
    logger.error('unhandled_error', { path: req.path, message: err.message });
    return res.status(500).json({ error: 'Erro interno' });
  };
}

function notFoundHandler(req, res) {
  res.status(404).json({ error: `Rota ${req.method} ${req.path} não encontrada` });
}

module.exports = { createErrorHandler, notFoundHandler };
