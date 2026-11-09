// Gateway de pagamento. Em dev é simulado: cartões iniciados em "4" são aprovados (regra herdada do legado).
const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });
const APPROVED_CARD_PREFIX = '4';

function createPaymentGateway({ apiKey, logger }) {
  return {
    async charge({ cardNumber, amount }) {
      // Só os 4 últimos dígitos vão para o log; a chave nunca é logada.
      logger.info('payment_processing', { card_last4: String(cardNumber).slice(-4), amount, live: Boolean(apiKey) });
      return String(cardNumber).startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    },
  };
}

module.exports = { createPaymentGateway, PAYMENT_STATUS };
