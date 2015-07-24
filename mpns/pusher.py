import logging
from collections import namedtuple

from zope.interface import implements, implementer

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, succeed, returnValue
from twisted.internet.ssl import PrivateCertificate, optionsForClientTLS
from twisted.web.iweb import IBodyProducer, IPolicyForHTTPS
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

from mpns.exceptions import (
    InvalidResponseError,
    HTTPError,
    DeliveryError,
    QueueFullError,
    SubscriptionExpiredError,
    DeviceDisconnectedError,
    ThrottlingLimitError
)


logger = logging.getLogger(__name__)


class NotificationStatus(
    namedtuple('NotificationStatus',
               ['notification', 'subscription', 'device'])):
    """
    Contains information extracted from gateway server response.
    """


class StringProducer(object):
    """
    Simple body producer pushing a in-memory string to a Twisted consumer.
    """
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


@implementer(IPolicyForHTTPS)
class NotificationPolicyForHTTPS(object):
    """
    TLS policy implementation for HTTPS clients, providing a client-side
    certificate for authentication against server.
    """
    def __init__(self, pem):
        if pem is None:
            self._clientCertificate = None
        else:
            self._clientCertificate = PrivateCertificate.loadPEM(pem)

    def creatorForNetloc(self, hostname, port):
        return optionsForClientTLS(hostname.decode('ascii'),
                                   clientCertificate=self._clientCertificate)


class Pusher(object):
    """
    Allows connecting to the MPNS gateway and sending notifications to the end
    devices.

    :param pem: a string containing PEM-formatted certificate used to
    authenticate the client against the gateway server. Only necessary for
    sending notifications to https based subscriptions.
    """

    PROCESSABLE_RESPONSES = [200, 404, 406, 412]

    RESPONSE_TO_ERROR = {
        400: 'Bad request',
        401: 'Unauthorized',
        405: 'Method not allowed',
        503: 'Service unavailable'
    }

    def __init__(self, pem=None):
        self._agent = Agent(reactor, NotificationPolicyForHTTPS(pem))

    @inlineCallbacks
    def send(self, notification):
        """
        Send prepared notification to the gateway server and fire some events
        based on the server's response. Raise an exception if the gateway
        rejected the request, the response could not be parsed, or we know the
        notification will never be delivered.

        :return an instance of NotificationStatus, containing notification,
        subscription and device statuses extracted from the response.
        """
        logger.debug('Sending request')

        body = StringProducer(notification.requestBody)
        headers = Headers(notification.requestHeaders)

        response = yield self._agent.request('POST', notification.requestUri,
                                             headers, body)

        logger.debug('Response code: %i', response.code)

        if response.code in self.PROCESSABLE_RESPONSES:
            returnValue(self._processResponse(response))
        else:
            self._processErrorResponse(response)

    @staticmethod
    def _extractHeader(response, name):
        header = response.headers.getRawHeaders(name)
        if header is not None and len(header) > 0:
            return header[0]
        else:
            return ''

    @classmethod
    def _processResponse(cls, response):
        status = NotificationStatus(
            notification=cls._extractHeader(response, 'X-NotificationStatus'),
            subscription=cls._extractHeader(response, 'X-SubscriptionStatus'),
            device=cls._extractHeader(response, 'X-DeviceConnectionStatus')
        )

        logger.debug('Notification ' + status.notification)
        logger.debug('Subscription ' + status.subscription)
        logger.debug('Device ' + status.device)

        extra = {'response code': response.code, 'status': status}

        if response.code == 200:
            if status.notification in ['Received', 'Suppressed']:
                return status
            elif status.notification == 'QueueFull':
                raise QueueFullError('Queue full', extra=extra)

        elif response.code == 404 and status.subscription == 'Expired':
            raise SubscriptionExpiredError('Subscription expired', extra=extra)

        elif response.code == 406:
            raise ThrottlingLimitError('Throttling limit hit', extra=extra)

        elif response.code == 412:
            raise DeviceDisconnectedError('Device disconnected', extra=extra)

        if status.notification == 'Dropped':
            raise DeliveryError('Dropped for unknown reason', extra=extra)
        else:
            raise InvalidResponseError('Invalid notification status',
                                       extra=extra)

    @staticmethod
    def _processErrorResponse(response):
        message = Pusher.RESPONSE_TO_ERROR.get(
            response.code, 'Unknown response code')

        raise HTTPError(message, {'response code': response.code})
