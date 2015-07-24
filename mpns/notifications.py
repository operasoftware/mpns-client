from mpns.exceptions import NotificationError


DELIVER_IMMEDIATELY = 'deliver_immediately'
DELIVER_WITHIN_450_S = 'deliver_within_450_s'
DELIVER_WITHIN_950_S = 'deliver_within_950_s'


class RawNotification(object):
    """
    Formatter for raw notifications. Its interpretation on the end device is
    totally application-dependent.

    :param uri: unique device URI.
    :param priority: desired notification priority, either DELIVER_IMMEDIATELY,
    DELIVER_WITHIN_450_S, or DELIVER_WITHIN_950_S.
    :param uuid: an optional UUID uniquely identifying the notification message
    :param body: a string containing payload to be sent within HTTP request.
    The structure of the payload is freely definable.
    """

    CLASS_HEADERS = {DELIVER_IMMEDIATELY: '3', DELIVER_WITHIN_450_S: '13',
                     DELIVER_WITHIN_950_S: '23'}

    def __init__(self, uri, **kwargs):
        self._uri = uri
        self._priority = kwargs.get('priority', DELIVER_IMMEDIATELY)
        self._body = kwargs.get('body')
        self._headers = {}
        self._setHeader('X-NotificationClass', self._classHeader())
        if 'uuid' in kwargs:
            self._setHeader('X-MessageID', kwargs['uuid'])

    @property
    def requestUri(self):
        """Return originate URI for HTTP request."""
        return self._uri

    @property
    def requestBody(self):
        """Return request body to be included within HTTP request."""
        return self._body

    @property
    def requestHeaders(self):
        """Return additional headers to be appended to HTTP request."""
        return self._headers

    def _setHeader(self, name, value):
        """Assign new value to additional headers table"""
        self._headers[name] = [value]

    def _classHeader(self):
        """
        Return required HTTP X-NotificationClass header value. There are
        different values for different notification types, so CLASS_HEADERS
        should be adjusted by derivative classes implementing other
        notifications.
        """
        if self._priority not in self.CLASS_HEADERS:
            raise NotificationError('Invalid priority value')
        else:
            return self.CLASS_HEADERS[self._priority]


class XmlNotification(RawNotification):
    """
    A base class for XML-based notification formatters. Generally should not
    be instantiated standalone.
    """

    def __init__(self, node, uri, **kwargs):
        super(XmlNotification, self).__init__(uri, **kwargs)
        self._setHeader('Content-Type', 'text/xml')
        self._node = node
        self._elements = []

    def _addElement(self, name, value):
        if value is not None:
            self._elements.append((name, value))

    XML_HEADER = ('<?xml version=\"1.0\" encoding=\"utf-8\"?>'
                  '<wp:Notification xmlns:wp=\"WPNotification\">'
                  '<wp:{0}>')

    XML_FOOTER = ('</wp:{0}>'
                  '</wp:Notification>')

    def _updateBody(self):
        xml = [self.XML_HEADER.format(self._node)]

        for e in self._elements:
            name, value = e
            xml.append('<wp:{0}>{1}</wp:{0}>'.format(name, value))

        xml.append(self.XML_FOOTER.format(self._node))

        self._body = ''.join(xml)


class ToastNotification(XmlNotification):
    """
    Formatter for toast notifications. See Windows Phone documentation for more
    information about its interpretation on the end device.

    :param uri: unique device URI.
    :param priority: desired notification priority, either DELIVER_IMMEDIATELY,
    DELIVER_WITHIN_450_S, or DELIVER_WITHIN_950_S.
    :param uuid: an optional UUID uniquely identifying the notification message
    :param text1: title of the toast notification.
    :param text2: content of the toast notification.
    :param param: additional parameters for deep linking to an application
    screen. See documentation for more details.
    :param sound: optional path to sound file to be played when notification
    arrives
    """

    CLASS_HEADERS = {DELIVER_IMMEDIATELY: '2', DELIVER_WITHIN_450_S: '12',
                     DELIVER_WITHIN_950_S: '22'}

    def __init__(self, uri, **kwargs):
        super(ToastNotification, self).__init__('Toast', uri, **kwargs)
        self._setHeader('X-WindowsPhone-Target', 'toast')
        self._addElement('Text1', kwargs.get('text1'))
        self._addElement('Text2', kwargs.get('text2'))
        self._addElement('Param', kwargs.get('param'))
        self._addElement('Sound', kwargs.get('sound'))
        self._updateBody()


class TileNotification(XmlNotification):
    """
    Formatter for tile notifications. See Windows Phone documentation for more
    information about its interpretation on the end device.

    :param uri: unique device URI.
    :param priority: desired notification priority, either DELIVER_IMMEDIATELY,
    DELIVER_WITHIN_450_S, or DELIVER_WITHIN_950_S.
    :param uuid: an optional UUID uniquely identifying the notification message
    :param title: title of the tile
    :param count: count to be displayed on the tile
    :param background: optional URI to a background image of the tile
    """

    # TODO: support for more advanced tile options

    CLASS_HEADERS = {DELIVER_IMMEDIATELY: '1', DELIVER_WITHIN_450_S: '11',
                     DELIVER_WITHIN_950_S: '21'}

    def __init__(self, uri, **kwargs):
        super(TileNotification, self).__init__('Tile', uri, **kwargs)
        self._setHeader('X-WindowsPhone-Target', 'token')
        self._addElement('Title', kwargs.get('title'))
        self._addElement('Count', kwargs.get('count'))
        self._addElement('BackgroundImage', kwargs.get('background'))
        self._updateBody()
