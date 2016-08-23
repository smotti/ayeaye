# Description

A service to send notifications about events via different channels (i.e.
email, sms, ...).

---

# Dependencies

## Development

* Vagrant
* Python packages/modules
  * arrow
  * Flask
  * setuptools

## Runtime

* Python packages/modules
  * arrow
  * Flask
  * setuptools (required for installation)
  * pip (required for installation of dependencies)

---

# Build

To build a distributable package:

```
$ python setup.py sdist
```

This will create a directory named **dist/** which contains a tar archive.

# Installation

Unpack the tar archive (artificate of the build step):

```
$ tar xzf ayeaye-<version>.tar.gz
```

Install it via the following command (note you'll need root privileges):

```
# python setup.py install
```

The previous command will install ayeaye and its required dependencies. An
executable script is copied to **/usr/local/bin/ayeaye**.

# Usage

```
$ ayeaye --help
usage: ayeaye [-h] [-l LISTEN] [-p PORT] [-d PATH] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -l LISTEN, --listen LISTEN
                        IP address the HTTP REST API should listen on
  -p PORT, --port PORT  The port of the HTTP REST API
  -d PATH, --database DBPATH
                        Path to the sqlite3 database
  -D UPLOAD_DIR, --uploadDir LOGPATH
                        Path to the temporary stored to-be-sent log files
  -m MAX_LEN, --maxLen SIZE(MB)
                        Maximum length for the content of a request
  -v, --verbose         Verbose output
```

---

# Contribute

* Clone repository

```
git clone git@gogs.medicustek.com:MantiS/notification-service.git
```

* Run VM via vagrant

```
vagrant up --provision
```

* Write unittest
* Modify code
* Run unittests
* Push if unittests passed

```
git push origin master
```

---

# Documentation

## REST API

The api exposes resources via JSON and only accepts JSON as data within
request bodies. Thus the header field **Content-Type** must be set to:

```
application/json
```

For reponses/requests containing data in their body.

### Status codes

For possible response codes refer to
[RFC7231](http://tools.ietf.org/html/rfc7231) and
[here](https://httpstatuses.com/).

### Errors

To indicate errors the status codes 4xx and 5xx are being used accordingly.
The response body to an error looks a follows:

```
{
    "time": "2016-03-28T16:31:33,123Z",
      "message": "A descriptive error message you can give to a dev",
        "type": "ERROR_TYPE"
}
```

The time conforms to ISO8601 and always represents UTC time and includes
milliseconds.

Note that **I'm a teaport** error is returned for http methods that are not
supported.

### Handlers

A notification handler represents a method on how to send a notification, i.e.
via email, sms, instant message, etc.
There a predefined handlers for: *email*.
A specific notification handler endpoint (i.e. /handlers/email) allows you to
create a new handler for a notification topic (tag).

#### GET /handlers/email

Get a list of email notification handlers.

##### URL

```
http://<host>/handlers/email
```

##### Example

###### Request

```
GET http://127.0.0.1/handlers/email
```

###### Result

```
STATUS 200
BODY [{"topic": "IRB",
       "settings": {"auth": 1, "server": "127.0.0.1", "port": 465,
                    "starttls": 0, "ssl": 1, "fromAddr": "docking@medicustek.com",
                    "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]}}]
```

#### GET /handlers/email/:topic

Get a specific email notification handlers.

##### URL

```
http://<host>/handlers/email
```

##### Example

###### Request

```
GET http://127.0.0.1/handlers/email/IRB
```

###### Result

```
STATUS 200
BODY [{"topic": "IRB",
       "settings": {"auth": 1, "server": "127.0.0.1", "port": 465,
                    "starttls": 0, "ssl": 1, "fromAddr": "docking@medicustek.com",
                    "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]}}]
```

#### POST /handlers/email

Create a new email notification handler for the specified topic (tag).

##### URL

```
http://<host>/handlers/email
```

##### Request Parameters

| Parameter (Value-Type) | Description |
| ---------------------- | ----------- |
| topic (str) | A unique topic name (tag) to identify this handler. It should only contain alphanumeric characters. |
| settings (json map) | A JSON map of settings (i.e. server, port, auth, ...) to use instead of global email handler settings (see below) |

##### Example

###### Request

```
POST http://127.0.0.1/handlers/email
BODY {"settings": {"starttls": 0, "auth": 1, "server": "127.0.0.1", "port": 465,
                   "ssl": 1, "fromAddr": "docking@medicustek.com",
                   "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]},
      "topic": "IRB"} 
```

###### Result

```
STATUS 200
BODY {"settings": {"starttls": 0, "auth": 1, "server": "127.0.0.1", "port": 465,
                   "ssl": 1, "fromAddr": "docking@medicustek.com",
                   "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]},
      "topic": "IRB"} 
```

#### PUT /handlers/email/:topic

Create a new email notification handler for the specified topic or update
an existing one.

##### URL

```
http://<host>/handlers/email
```

##### Request Parameters

| Parameter (Value-Type) | Description |
| ---------------------- | ----------- |
| settings (json map) | A JSON map of settings (i.e. server, port, auth, ...) to use instead of global email handler settings (see below) |

##### Example

###### Request

```
PUT http://127.0.0.1/handlers/email/IRB
BODY {"settings": {"starttls": 0, "auth": 1, "server": "127.0.0.1", "port": 465,
                   "ssl": 1, "fromAddr": "docking@medicustek.com",
                   "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]}}
```

###### Result

```
STATUS 200
BODY {"settings": {"starttls": 0, "auth": 1, "server": "127.0.0.1", "port": 465,
                   "ssl": 1, "fromAddr": "docking@medicustek.com",
                   "toAddr": ["employee0@medicustek.com, cra@medicustek.com"]},
      "topic": "IRB"} 
```


### Settings

The settings resources represent global settings for notification handlers
that will be used if no handler specific settings have been specified.

#### GET /settings/email

Get a the global settings used by email notification handlers.

##### URL

```
http://<host>/settings/email
```
##### Example

###### Request

```
GET http://127.0.0.1/settings/email
```

###### Result

```
STATUS 200
BODY {"port": 25, "starttls": 1, "server": "127.0.0.1", "ssl": 0, "auth": 1}
```

#### PUT /settings/email

Set global emil notification handler settings.

##### URL

```
http://<host>/settings/email
```

##### Request parameters

| Parameter (Value-Type) | Description |
| ---------------- | ----------- |
| server (str) | The address of the email server (required) |
| port (int) | The port of the email service on the server (required) |
| ssl (bool) | If SMPTS should be used for the connection (required) |
| auth (bool) | If SMTP AUTH should be performed (required) |
| starttls (bool) | If STARTTLS should be used to encrypt the connection (required) |
| user (str) | The username to use for SMTP AUTH (optional, required if auth is true) |
| password (str) | The password to use for SMTP AUTH (optional, required if auth is true) |
| toAddr ([str]) | A list of email addresses to which to send the notification (required) |
| fromAddr (str) | From which email to send the notification (required) |

##### Example

###### Request

```
PUT http://127.0.0.1/settings/email
BODY {"server": "127.0.0.1", "port": 25, "ssl": 0, "auth": 1, "starttls": 1}
```

###### Result

```
STATUS 200
BODY {"server": "127.0.0.1", "auth": 1, "starttls": 1, "ssl": 0, "port": 25}
```

### Notifications

Notifications are categorized by handler topic and represent notifications
send as specified by the handler.

#### GET /notifications/

A list of notifications that may be limited by a specified time range.

##### URL

```
http://<host>/notifications/
```
##### Request parameters

The following request parameters may be provided as url query strings.

| Parameter | Description |
| --------- | ----------- |
| fromTime  | From what time in point onwards notification should be retrieved |
| toTime | The point in time up to which to receive notifications |

##### Example

###### Request

```
GET http://127.0.0.1/notifications/
```

###### Result

```
STATUS 200
BODY [{"content": "Patient with ID 1233 checked in", "topic": "IRB",
       "title": "Patient Check-In", "time": 10},
      {"content": "Patient with ID 1233 checked in", "topic": "IRB",
       "title": "Patient Check-In", "time": 15},
      {"content": "Patient with ID 1233 checked in", "topic": "IRB",
       "title": "Patient Check-In", "time": 20}]
```

#### GET /notifications/:topic

Get a list of notifications of the specified topic.

##### URL

```
http://<host>/notifications/
```
##### Request parameters

The following request parameters may be provided as url query strings.

| Parameter | Description |
| --------- | ----------- |
| fromTime  | From what time in point onwards notification should be retrieved |
| toTime | The point in time up to which to receive notifications |

##### Example

###### Request

```
GET http://127.0.0.1/notifications/IRB?fromTime=15&toTime=30
```

###### Result

```
STATUS 200
BODY [{"content": "Patient with ID 1233 checked in", "topic": "IRB",
       "title": "Patient Check-In", "time": 15},
      {"content": "Patient with ID 1233 checked in", "topic": "IRB",
       "title": "Patient Check-In", "time": 20}]
```

#### POST /notifications/:topic

Send a notification for the specified topic.

##### URL

```
http://<host>/notifications/
```

##### Request parameters

| Parameter (Value-Type) | Description |
| ---------------------- | ----------- |
| title (str) | The title/subject of the notification |
| content (str) | The content of the notification |

##### Example

###### Request

```
POST http://127.0.0.1/notifications/IRB
BODY {"title": "Patient Check-In", "content": "Patient with ID 1233 checked in"}
```

###### Result

```
STATUS 200
```

#### POST /notifications/log/:topic

Send a log notification with the log attachment for the specified topic.

Due to the need of uploading files, the **Content-Type** must set to:

```
multipart/form-data
```

##### URL

```
http://<host>/notifications/log/
```

##### Request multipart post data

| Key | Description |
| --- | ----------- |
| title (str) | The title/subject of the notification |
| content (str) | The content of the notification |
| file(list) | List of log file to be sent |

##### Example

###### Request

```
POST http://127.0.0.1/notifications/log/IRB
BODY

Content-Disposition: form-data; name="title"
    Log file 20161223
Content-Disposition: form-data; name="content"
    In the attachement is the log files
Content-Disposition: form-data; name="file"; filename="dashboard.1.log"
    This is the file content #1
Content-Disposition: form-data; name="file"; filename="dashboard.2.log"
    This is the file content #2

```

###### Result

```
STATUS 200
```
