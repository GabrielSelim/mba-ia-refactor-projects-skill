// Configuração lida do ambiente. Nenhum segredo real no código.
const config = Object.freeze({
  port: Number(process.env.PORT) || 3000,
  dbPath: process.env.DB_PATH || ':memory:',
  // Chave do gateway de pagamento: vem do ambiente (vazia = gateway simulado em dev).
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
  logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
