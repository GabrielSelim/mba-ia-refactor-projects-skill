// Camada View: mapeia URL + método → controller.
const express = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function buildRouter(controllers) {
  const router = express.Router();
  router.post('/api/checkout', asyncHandler(controllers.checkout.checkout));
  router.get('/api/admin/financial-report', asyncHandler(controllers.report.financialReport));
  router.delete('/api/users/:id', asyncHandler(controllers.user.deleteUser));
  return router;
}

module.exports = { buildRouter };
