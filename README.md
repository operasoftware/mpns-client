# Microsoft Push Notification Service client

## Overview
*MPNS-client* is an implementation of provider-side client for Microsoft Push
Notification Service, based on [official WP8 documentation]
(https://msdn.microsoft.com/en-us/library/windows/apps/ff402558.aspx). It uses
[Twisted networking engine](https://twistedmatrix.com).

## Features
* Preparing Raw, Toast, and Tile notifications
* Sending prepared notifications to the gateway server
* Extracting information about device and notification state from gateway
response

## Requirements
* Python>=2.7
* Twisted>=15.0.0

## Usage example

```python
import logging
from mpns.notifications import ToastNotification
from mpns.pusher import Pusher
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

uri = '*PASTE YOUR SUBSCRIPTION URI HERE*'


@inlineCallbacks
def main(reactor):
    notification = ToastNotification(uri, text1='Hello!', text2='Wassup?')
    pusher = Pusher()
    yield pusher.send(notification)

react(main)

```

If everything was setup correctly, you should see in console something like
this:
```
Sending request
Response code: 200
Device Connected
Notification Received
Subscription Active
```
Then a notification should pop up on your phone.

## Contributing
You are highly encouraged to participate in the development, simply use
GitHub's fork/pull request system.
