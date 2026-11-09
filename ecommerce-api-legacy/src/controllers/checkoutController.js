// Fluxo de checkout: valida, cobra e matricula de forma atômica.
const { NotFoundError, PaymentDeniedError, ValidationError } = require('../errors');
const { PAYMENT_STATUS } = require('../services/paymentGateway');

function createCheckoutController({ db, models, paymentGateway, passwordHasher, logger }) {
  async function checkout(req, res) {
    // Campos públicos do contrato mantidos (usr, eml, pwd, c_id, card); nomes internos descritivos.
    const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body || {};
    if (!name || !email || !courseId || !cardNumber) throw new ValidationError('Bad Request');

    const course = await models.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const existingUser = await models.users.findByEmail(email);
    if (!existingUser && !password) throw new ValidationError('Senha obrigatória para novo usuário');

    const status = await paymentGateway.charge({ cardNumber, amount: course.price });
    if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

    const enrollmentId = await db.transaction(async () => {
      const userId = existingUser
        ? existingUser.id
        : await models.users.create({ name, email, passwordHash: passwordHasher.hash(password) });
      const newEnrollmentId = await models.enrollments.create({ userId, courseId: course.id });
      await models.payments.create({ enrollmentId: newEnrollmentId, amount: course.price, status });
      await models.auditLogs.record(`Checkout curso ${course.id} por ${userId}`);
      return newEnrollmentId;
    });

    logger.info('checkout_completed', { course_id: course.id, enrollment_id: enrollmentId });
    res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
  }

  return { checkout };
}

module.exports = { createCheckoutController };
