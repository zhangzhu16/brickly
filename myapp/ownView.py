import json
import os

from django.conf import settings
from django.core.validators import validate_email, ValidationError
from django.http import Http404, FileResponse
from django.http.response import HttpResponse
from django.utils.translation import ugettext as _
from rest_framework import permissions
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.views import APIView

from .datetime import Datetime


class StatusCode:
    SUCCESS = 200
    SUCCESS_CREATED = 201
    SUCCESS_ACCEPTED = 202
    SUCCESS_CONFIRM = 210
    SUCCESS_NEED_CONFIRM = 209
    SUCCESS_RESET = 211

    WARNING = 300
    WARNING_NOT_MODIFIED = 304
    WARNING_MODIFIED = 306

    ERROR = 400
    ERROR_UNAUTHORIZED = 401
    ERROR_FORBIDDEN = 403
    ERROR_NOT_FOUND = 404
    ERROR_NOT_ALLOWED = 405
    ERROR_NOT_ACCEPTABLE = 406
    ERROR_CONFLICT = 409
    ERROR_VALIDATION = 410
    ERROR_NOT_SUPPORTED = 415
    ERROR_NOT_SATISFIABLE = 416

    SERVER_ERROR = 500
    SERVER_ERROR_NOT_IMPLEMENTED = 501

    names = {
        SUCCESS: 'success',
        SUCCESS_CREATED: 'success_created',
        SUCCESS_ACCEPTED: 'success_accepted',
        SUCCESS_CONFIRM: 'success_confirm',
        SUCCESS_NEED_CONFIRM: 'success_need_confirm',
        SUCCESS_RESET: 'success_reset',

        WARNING: 'warning',
        WARNING_NOT_MODIFIED: 'warning_not_modified',
        WARNING_MODIFIED: 'warning_modified',

        ERROR: 'error',
        ERROR_UNAUTHORIZED: 'error_unauthorized',
        ERROR_FORBIDDEN: 'error_forbidden',
        ERROR_NOT_FOUND: 'error_not_found',
        ERROR_NOT_ALLOWED: 'error_not_allowed',
        ERROR_NOT_ACCEPTABLE: 'error_not_acceptable',
        ERROR_CONFLICT: 'error_conflict',
        ERROR_VALIDATION: 'error_validation',
        ERROR_NOT_SUPPORTED: 'error_not_supported',
        ERROR_NOT_SATISFIABLE: 'error_not_satisfiable',

        SERVER_ERROR: 'server_error',
        SERVER_ERROR_NOT_IMPLEMENTED: 'server_error_not_implemented',
    }


class RestViewError(Exception):
    def __init__(self, status_code, err_msg):
        self._status_code = status_code
        self._err_msg = err_msg
        super(RestViewError, self).__init__(err_msg)

    @property
    def status_code(self):
        return self._status_code

    @property
    def err_msg(self):
        return self._err_msg


class InvalidArgumentError(RestViewError):
    def __init__(self, err_msg):
        super(InvalidArgumentError, self).__init__(StatusCode.ERROR, err_msg)


class MissingArgumentError(InvalidArgumentError):
    pass


class RestView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def __init__(self):
        super(RestView, self).__init__()
        self._request = None
        self._user = None

    def handle_exception(self, exc):
        response = super(RestView, self).handle_exception(exc)
        if response.status_code == 403:
            return self.error(StatusCode.ERROR_UNAUTHORIZED, _('Access denied'))
        return response

    def get_json_param(self, name, expected_type,
                       err_msg="Please enter a valid structure",
                       default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))
        if not isinstance(value, expected_type):
            raise InvalidArgumentError(err_msg)
        return value

    def get_string_param(self, name,
                         err_msg="Please enter a valid string",
                         default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))
        if not isinstance(value, str):
            raise InvalidArgumentError(err_msg)
        return value

    def get_date_param(self, name,
                       err_msg="Please enter a valid date",
                       default=None, required=True, detail=False):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))

        try:
            return Datetime.strptime(value, '%Y-%m-%d') if not detail else Datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            raise InvalidArgumentError(err_msg)

    def get_bool_param(self, name,
                       err_msg="Please enter a valid boolean flag",
                       default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))
        if type(value) is not bool:
            value = value.lower() in ("yes", "true", "1")
        if not isinstance(value, bool):
            raise InvalidArgumentError(err_msg)
        return value

    def get_int_param(self, name,
                      err_msg="Please enter a valid integer",
                      default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))
        if not isinstance(value, int):
            try:
                value = int(value)
            except:
                raise InvalidArgumentError(err_msg)
        return value

    def get_email_param(self, name,
                        err_msg="Please enter a valid email",
                        default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        try:
            value = self._request.data.get(name, self._request.query_params.get(name))
            validate_email(value)
            email_name, domain_part = value.strip().rsplit('@', 1)
            return '@'.join([email_name, domain_part.lower()])
        except ValidationError:
            raise InvalidArgumentError(err_msg)

    def get_phone_param(self, name,
                        err_msg="Please enter a valid phone number",
                        default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        value = self._request.data.get(name, self._request.query_params.get(name))
        phone_number = value.strip()
        return phone_number

    def get_verification_code(self, name,
                              err_msg="Please enter a valid verification code",
                              default=None, required=True):
        if name not in self._request.data and name not in self._request.query_params:
            if required:
                raise MissingArgumentError(err_msg)
            return default

        code = self._request.data.get(name, self._request.query_params.get(name))
        if len(code) != 4:
            raise InvalidArgumentError(err_msg)
        return code

    def _response(self, response):
        pass

    def _render_response(self, status_code, msg, result):
        body = {
            'status': StatusCode.names[status_code],
            'message': msg,
            'result': result,
        }
        http_response = HttpResponse(content=json.dumps(body, cls=JSONEncoder),
                                     content_type='application/json',
                                     status=status_code)
        self._response(http_response)
        return http_response

    def error(self, status_code, msg):
        assert StatusCode.ERROR <= status_code < StatusCode.SERVER_ERROR
        return self._render_response(status_code, msg, None)

    def success(self, result, msg=_('Success'), status_code=StatusCode.SUCCESS):
        assert StatusCode.SUCCESS <= status_code < StatusCode.WARNING
        return self._render_response(status_code, msg, result)

    def post(self, request):
        try:
            self._request = request
            self._user = self._request.user
            return self._post()
        except RestViewError as e:
            return self.error(e.status_code, e.err_msg or str(e))

    def _post(self):
        return self.error(StatusCode.ERROR_NOT_SUPPORTED, 'not implemented')

    def patch(self, request):
        try:
            self._request = request
            self._user = self._request.user
            return self._patch()
        except RestViewError as e:
            return self.error(e.status_code, e.err_msg or str(e))

    def _patch(self):
        return self.error(StatusCode.ERROR_NOT_SUPPORTED, 'not implemented')

    def delete(self, request):
        try:
            self._request = request
            self._user = self._request.user
            return self._delete()
        except RestViewError as e:
            return self.error(e.status_code, e.err_msg or str(e))

    def _delete(self):
        return self.error(StatusCode.ERROR_NOT_SUPPORTED, 'not implemented')

    def get(self, request):
        try:
            self._request = request
            self._user = self._request.user
            return self._get()
        except RestViewError as e:
            return self.error(e.status_code, e.err_msg or str(e))

    def _get(self):
        return self.error(StatusCode.ERROR_NOT_SUPPORTED, 'not implemented')


class EmptyView(RestView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def _get(self):
        return self.success(0)


