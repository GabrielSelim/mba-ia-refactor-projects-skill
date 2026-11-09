// Composition root: monta a aplicação a partir das dependências injetadas.
const express = require('express');
const { createModels } = require('./models');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { buildRouter } = require('./routes');
const { createErrorHandler, notFoundHandler } = require('./middlewares/errorHandler');

function createApp({ db, paymentGateway, passwordHasher, logger }) {
  const models = createModels(db);
  const controllers = {
    checkout: createCheckoutController({ db, models, paymentGateway, passwordHasher, logger }),
    report: createReportController({ models }),
    user: createUserController({ db, models, logger }),
  };

  const app = express();
  app.use(express.json());
  app.use(buildRouter(controllers));
  app.use(notFoundHandler);
  app.use(createErrorHandler(logger));
  return app;
}

module.exports = { createApp };
