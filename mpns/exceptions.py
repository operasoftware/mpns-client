class NotificationError(Exception):
    """To be raised upon failures on notification formatting."""


class NotificationPusherError(Exception):
    """
    To be raised upon failures on communication with a notification gateway.
    """
    def __init__(self, message=None, extra=None):
        super(NotificationPusherError, self).__init__(message)
        self.extra = extra


class InvalidResponseError(NotificationPusherError):
    """Raised when gateway server returned an unparseable response."""


class HTTPError(NotificationPusherError):
    """
    Raised when gateway server refused to process the request and returned a
    HTTP error code.
    """


class DeliveryError(NotificationPusherError):
    """
    Raised when gateway server understood the request, but assured that the
    notification will never be delivered.
    """


class SubscriptionExpiredError(DeliveryError):
    """Raised when the subscription URI expired and should be deleted."""


class QueueFullError(DeliveryError):
    """
    Raised when the corresponding notification queue is full and notifications
    are dropped.
    """


class DeviceDisconnectedError(DeliveryError):
    """
    Raised when the device was disconnected for extended period of time and
    notifications are dropped.
    """


class ThrottlingLimitError(DeliveryError):
    """
    Raised when an unauthenticated pusher has reached the per-day throttling
    limit for a subscription, or when a pusher (authenticated or
    unauthenticated) has sent too many notifications per second.
    """
