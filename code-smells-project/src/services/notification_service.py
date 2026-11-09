"""Notificações (e-mail, SMS, push) desacopladas do fluxo HTTP.

Hoje os canais são simulados via log; trocar por uma integração real não exige mudar controllers.
"""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def notify_order_created(self, pedido_id, usuario_id):
        logger.info("email_enviado pedido=%s usuario=%s", pedido_id, usuario_id)
        logger.info("sms_enviado pedido=%s", pedido_id)
        logger.info("push_enviado pedido=%s", pedido_id)

    def notify_order_status(self, pedido_id, novo_status):
        logger.info("notificacao_status pedido=%s status=%s", pedido_id, novo_status)
