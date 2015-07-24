from twisted.trial.unittest import TestCase

from mpns.notifications import (
    RawNotification,
    XmlNotification,
    ToastNotification,
    TileNotification,
    DELIVER_IMMEDIATELY,
    DELIVER_WITHIN_450_S,
    DELIVER_WITHIN_950_S,
    NotificationError
)


class NotificationTestCase(TestCase):

    TEST_URI = 'http://foo/bar'
    TEST_UUID = 'de305d54-75b4-431b-adb2-eb6b9e546014'

    def test_uri(self):
        notification = RawNotification(self.TEST_URI)
        self.assertEqual(notification.requestUri, self.TEST_URI)

    def test_body_empty(self):
        notification = RawNotification(self.TEST_URI)
        self.assertEqual(notification.requestBody, None)

    def test_body_defined(self):
        notification = RawNotification(self.TEST_URI, body='foo')
        self.assertEqual(notification.requestBody, 'foo')

    def test_set_header(self):
        notification = RawNotification(self.TEST_URI)
        notification._setHeader('foo', 'bar')
        self.assertEqual(notification.requestHeaders['foo'], ['bar'])

    def test_class_header_nonexisting(self):
        with self.assertRaises(NotificationError):
            RawNotification(self.TEST_URI, priority=999)

    def test_class_header_raw_high_priority(self):
        notification = RawNotification(self.TEST_URI,
                                       priority=DELIVER_IMMEDIATELY)
        self.assertEqual(notification._classHeader(), '3')

    def test_class_header_toast_mid_priority(self):
        notification = ToastNotification(self.TEST_URI,
                                         priority=DELIVER_WITHIN_450_S)
        self.assertEqual(notification._classHeader(), '12')

    def test_class_header_tile_low_priority(self):
        notification = TileNotification(self.TEST_URI,
                                        priority=DELIVER_WITHIN_950_S)
        self.assertEqual(notification._classHeader(), '21')

    def test_target_header_raw(self):
        notification = RawNotification(self.TEST_URI)
        self.assertFalse('X-WindowsPhone-Target' in
                         notification.requestHeaders)

    def test_target_header_toast(self):
        notification = ToastNotification(self.TEST_URI)
        self.assertEqual(notification.requestHeaders['X-WindowsPhone-Target'],
                         ['toast'])

    def test_target_header_tile(self):
        notification = TileNotification(self.TEST_URI)
        self.assertEqual(notification.requestHeaders['X-WindowsPhone-Target'],
                         ['token'])

    def test_uuid(self):
        notification = ToastNotification(self.TEST_URI, uuid=self.TEST_UUID)
        self.assertEqual(notification.requestHeaders['X-MessageID'],
                         [self.TEST_UUID])

    def test_xml_content_type(self):
        notification = XmlNotification('foo', self.TEST_URI)
        self.assertEqual(notification.requestHeaders['Content-Type'],
                         ['text/xml'])

    def test_xml_body(self):
        notification = XmlNotification('foo', self.TEST_URI)
        notification._addElement('bar', 'baz')
        notification._updateBody()
        body = ''.join([XmlNotification.XML_HEADER.format('foo'),
                        '<wp:bar>baz</wp:bar>',
                        XmlNotification.XML_FOOTER.format('foo')])
        self.assertEqual(body, notification.requestBody)
