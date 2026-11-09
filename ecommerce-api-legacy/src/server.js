// Entry point: cria as dependências concretas, inicializa o banco e sobe o servidor.
const config = require('./config');
const { openDatabase } = require('./database/connection');
const { initSchema } = require('./database/schema');
const { createLogger } = require('./services/logger');
const { createPasswordHasher } = require('./services/passwordHasher');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createApp } = require('./app');

async function main() {
  const logger = createLogger(config.logLevel);
  const db = openDatabase(config.dbPath);
  const passwordHasher = createPasswordHasher();
  const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });

  await initSchema(db, { passwordHasher });

  const app = createApp({ db, paymentGateway, passwordHasher, logger });
  app.listen(config.port, () => logger.info(`LMS API rodando na porta ${config.port}`));
}

main().catch((err) => {
  console.error('Falha ao iniciar a aplicação:', err);
  process.exit(1);
});
