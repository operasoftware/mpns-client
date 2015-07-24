from mock import Mock
from twisted.trial.unittest import TestCase

from mpns.pusher import (
    Pusher,
    InvalidResponseError,
    HTTPError,
    QueueFullError,
    SubscriptionExpiredError,
    DeviceDisconnectedError,
    ThrottlingLimitError
)


class PusherTestCase(TestCase):

    TEST_URI = 'http://foo/bar'

    def _create_mocked_notification(self):
        notification = Mock()
        notification.requestUri = self.TEST_URI
        notification.requestBody = 'foo'
        notification.requestHeaders = {'X-NotificationClass': ['3']}
        return notification

    def _create_mocked_response(self, code=200, notification='Received',
                                subscription='Active', device='Connected'):
        response = Mock()
        response.code = code
        response.MOCKED_HEADERS = {
            'X-NotificationStatus': [notification],
            'X-SubscriptionStatus': [subscription],
            'X-DeviceConnectionStatus': [device]
        }
        response.headers.getRawHeaders = Mock(
            side_effect=lambda name: response.MOCKED_HEADERS.get(name))
        return response

    def test_extract_header_defined(self):
        pusher = Pusher()
        resp = self._create_mocked_response()
        self.assertEqual(pusher._extractHeader(resp, 'X-NotificationStatus'),
                         'Received')

    def test_extract_header_missing(self):
        pusher = Pusher()
        resp = self._create_mocked_response()
        self.assertEqual(pusher._extractHeader(resp, 'foo'), '')

    def _assert_raises_HTTPError_with_extras(self, code):
        pusher = Pusher()
        resp = self._create_mocked_response(code=code)
        try:
            pusher._processErrorResponse(resp)
            self.assertFail()
        except HTTPError as error:
            self.assertEqual(code, error.extra['response code'])
            if code in Pusher.RESPONSE_TO_ERROR:
                self.assertEqual(Pusher.RESPONSE_TO_ERROR[code],
                                 error.message)
            else:
                self.assertEqual('Unknown response code', error.message)

    def test_process_error_response_400(self):
        self._assert_raises_HTTPError_with_extras(400)

    def test_process_error_response_401(self):
        self._assert_raises_HTTPError_with_extras(401)

    def test_process_error_response_405(self):
        self._assert_raises_HTTPError_with_extras(405)

    def test_process_error_response_503(self):
        self._assert_raises_HTTPError_with_extras(503)

    def test_process_error_response_unknown(self):
        self._assert_raises_HTTPError_with_extras(500)

    def test_process_response_unknown_status(self):
        pusher = Pusher()
        response = self._create_mocked_response(notification='foo')
        with self.assertRaises(InvalidResponseError):
            pusher._processResponse(response)

    def test_process_response_received(self):
        pusher = Pusher()
        response = self._create_mocked_response()
        status = pusher._processResponse(response)
        self.assertEqual(status.notification, 'Received')
        self.assertEqual(status.subscription, 'Active')
        self.assertEqual(status.device, 'Connected')

    def test_proces_response_suppressed(self):
        pusher = Pusher()
        response = self._create_mocked_response(notification='Suppressed')
        status = pusher._processResponse(response)
        self.assertEqual(status.notification, 'Suppressed')

    def test_process_response_queue_full(self):
        pusher = Pusher()
        response = self._create_mocked_response(notification='QueueFull')
        with self.assertRaises(QueueFullError):
            pusher._processResponse(response)

    def test_process_response_expired(self):
        pusher = Pusher()
        response = self._create_mocked_response(code=404,
                                                notification='Dropped',
                                                subscription='Expired')
        with self.assertRaises(SubscriptionExpiredError):
            pusher._processResponse(response)

    def test_process_response_disconnected(self):
        pusher = Pusher()
        response = self._create_mocked_response(code=412,
                                                notification='Dropped',
                                                device='Disconnected')
        with self.assertRaises(DeviceDisconnectedError):
            pusher._processResponse(response)

    def test_process_response_throttled(self):
        pusher = Pusher()
        response = self._create_mocked_response(code=406,
                                                notification='Dropped')
        with self.assertRaises(ThrottlingLimitError):
            pusher._processResponse(response)

    def test_send_processable(self):
        pusher = Pusher()
        notification = self._create_mocked_notification()
        response = self._create_mocked_response()

        pusher._agent.request = Mock(return_value=response)
        pusher._processResponse = Mock()
        pusher._processErrorResponse = Mock()

        pusher.send(notification)

        pusher._processResponse.assert_called_once_with(response)
        self.assertFalse(pusher._processErrorResponse.called)

    def test_send_unprocessable(self):
        pusher = Pusher()
        notification = self._create_mocked_notification()
        response = self._create_mocked_response(code=400)

        pusher._agent.request = Mock(return_value=response)
        pusher._processResponse = Mock()
        pusher._processErrorResponse = Mock()

        pusher.send(notification)

        pusher._processErrorResponse.assert_called_once_with(response)
        self.assertFalse(pusher._processResponse.called)
