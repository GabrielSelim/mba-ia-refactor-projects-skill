// Exclusão de usuário em cascata (pagamentos → matrículas → usuário) dentro de uma transação.
const { NotFoundError, ValidationError } = require('../errors');

function createUserController({ db, models, logger }) {
  async function deleteUser(req, res) {
    const userId = Number(req.params.id);
    if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError('id inválido');

    const user = await models.users.findById(userId);
    if (!user) throw new NotFoundError('Usuário não encontrado');

    await db.transaction(async () => {
      await models.payments.deleteByUser(userId);
      await models.enrollments.deleteByUser(userId);
      await models.users.deleteById(userId);
    });

    logger.info('user_deleted', { user_id: userId });
    res.status(200).json({ msg: 'Usuário deletado com sucesso' });
  }

  return { deleteUser };
}

module.exports = { createUserController };
