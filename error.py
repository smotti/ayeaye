import arrow

class Error(Exception): pass


def genError(className, httpCode, level, errorType):
    def __init__(self, msg):
        self.time = str(arrow.utcnow())
        self.msg = msg

    def toDict(self):
        return {'type': self.type, 'time': self.time, 'msg': self.msg}

    def toStr(self):
        return self.type + ': ' + self.msg

    return type(className, (Error, ), {
        'code': httpCode,
        'type': errorType,
        'level': level,
        'toDict': toDict,
        '__init__': __init__,
        '__str__': toStr,
    })


MissingAttributeError = genError('MissingAttributeError', 400, 40, 'MISSING_ATTRIBUTE')
UnknownAttributeError = genError('UnknownAttributeError', 400, 40, 'UNKOWN_ATTRIBUTE')
InvalidAttributeTypeError = genError('InvalidAttributeTypeError', 400, 40, 'INVALID_ATTRIBUTE_TYPE')
BadRequestError = genError('BadRequestError', 400, 40, 'BAD_REQUEST')
AuthorizationError = genError('AuthorizationError', 401, 40, 'AUTHORIZATION_ERROR')
AuthenticationError = genError('AuthenticationError', 403, 40, 'AUTHENTICATION_ERROR')
NotFoundError = genError('NotFoundError', 404, 30, 'NOT_FOUND')
TimeoutError = genError('TimeoutError', 408, 40,'TIMEOUT')
AlreadyExistsError = genError('AlreadyExistsError', 409, 30, 'ALREADY EXISTS')
ConstraintViolationError = genError('ConstraintViolationError', 412, 30, 'CONSTRAINT_VIOLATION')
TeapotError = genError('TeapotError', 418, 10, 'TEAPOT')
LimitExceededError = genError('LimitExceededError', 429, 30, 'LIMIT_EXCEEDED')
InternalError = genError('InternalError', 500, 50, 'INTERNAL_ERROR')
TransactionError = genError('TransactionError', 500, 40, 'TRANSACTION_ERROR')
SearchError = genError('SearchError', 500, 30, 'SEARCH_ERROR')
UnknownError = genError('UnkownError', 500, 50, 'UNKNOWN_ERROR')
AbortError = genError('AbortError', 500, 50, 'ABORT')
BusyError = genError('BusyError', 503, 40, 'BUSY')
UnavailableError = genError('UnavailableError', 503, 40, 'UNAVAILABLE')
MethodNotAllowedError = genError('MethodNotAllowed', 405, 40, 'METHOD_NOT_ALLOWED')
