# todo: make this do something or use built-in exception?
class ValidationError(Exception):
    pass

class StringValidator(object):

    def __call__(self, value):

        if type(value) not in [str, unicode]:
            raise ValidationError('Not a valid string: <{0}>'.format(value))

class TypeValidator(object):

    def __init__(self, _type):
        self._type = _type

    def __call__(self, value):
        if not isinstance(value, self._type):
            raise Exception(
                'Expected a value of type {}; received value {} of type {}'.format(
                    self._type, value, type(value)
                )
            )

validate_integer = TypeValidator(int)
validate_float = TypeValidator(float)
validate_boolean = TypeValidator(bool)

from ..fields import List
validate_list = TypeValidator(List)

import datetime
validate_datetime = TypeValidator(datetime.datetime)

# # class MinLengthValidator(StringValidator):
# class MinLengthValidator(object):
#
#     def __init__(self, min_length):
#
#         self.min_length = min_length
#
#     def __call__(self, value):
#
#         # super(MinLengthValidator, self).__call__(value)
#         if len(value) < self.min_length:
#             raise ValidationError(
#                 'Length must be at least {0}; received value <{1}> of length {2}'.format(
#                     self.min_length,
#                     value,
#                     len(value)
#                 )
#             )
#
# # class MaxLengthValidator(StringValidator):
# class MaxLengthValidator(object):
#
#     def __init__(self, max_length):
#
#         self.max_length = max_length
#
#     def __call__(self, value):
#
#         # super(MaxLengthValidator, self).__call__(value)
#         if len(value) > self.max_length:
#             raise ValidationError(
#                 'Length must be less than or equal to {0}; received value <{1}> of length {2}'.format(
#                     self.max_length,
#                     value,
#                     len(value)
#                 )
#             )


# Adapted from Django RegexValidator
import re
class RegexValidator(StringValidator):

    def __init__(self, regex=None, flags=0):

        if regex is not None:
            self.regex = re.compile(regex, flags=flags)

    def __call__(self, value):

        super(RegexValidator, self).__call__(value)
        if not self.regex.search(value):
            raise ValidationError(
                'Value must match regex {0} and flags {1}; received value <{2}>'.format(
                    self.regex.pattern,
                    self.regex.flags,
                    value
                )
            )

# Adapted from Django URLValidator
from urlparse import urlsplit, urlunsplit
class URLValidator(RegexValidator):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    # message = _('Enter a valid URL.')

    def __call__(self, value):
        try:
            super(URLValidator, self).__call__(value)
        except ValidationError as e:
            # Trivial case failed. Try for possible IDN domain
            if value:
                # value = force_text(value)
                scheme, netloc, path, query, fragment = urlsplit(value)
                try:
                    netloc = netloc.encode('idna').decode('ascii')  # IDN -> ACE
                except UnicodeError:  # invalid domain part
                    raise e
                url = urlunsplit((scheme, netloc, path, query, fragment))
                super(URLValidator, self).__call__(url)
            else:
                raise
        else:
            pass
            # url = value

class BaseValidator(object):
    compare = lambda self, a, b: a is not b

    def __init__(self, limit_value):
        self.limit_value = limit_value

    def __call__(self, value):
        if self.compare(value, self.limit_value):
            raise ValidationError('Received bad value: <{}>.'.format(value))

class MaxValueValidator(BaseValidator):
    compare = lambda self, a, b: a > b

class MinValueValidator(BaseValidator):
    compare = lambda self, a, b: a < b

class MinLengthValidator(BaseValidator):
    compare = lambda self, a, b: len(a) < b

class MaxLengthValidator(BaseValidator):
    compare = lambda self, a, b: len(a) > b

class BaseValidator(object):

    compare = lambda self, a, b: a is not b
    clean = lambda self, x: x
    message = 'Ensure this value is %(limit_value)s (it is %(show_value)s).'
    code = 'limit_value'

    def __init__(self, limit_value):
        self.limit_value = limit_value

    def __call__(self, value):
        cleaned = self.clean(value)
        params = {'limit_value': self.limit_value, 'show_value': cleaned}
        if self.compare(cleaned, self.limit_value):
            raise ValidationError(self.message.format(**params))


class MaxValueValidator(BaseValidator):

    compare = lambda self, a, b: a > b
    message = 'Ensure this value is less than or equal to {limit_value}.'
    code = 'max_value'


class MinValueValidator(BaseValidator):

    compare = lambda self, a, b: a < b
    message = 'Ensure this value is greater than or equal to {limit_value}.'
    code = 'min_value'


class MinLengthValidator(BaseValidator):

    compare = lambda self, a, b: a < b
    clean = lambda self, x: len(x)
    message = 'Ensure this value has length of at least {limit_value} (it has length {show_value}).'
    code = 'min_length'


class MaxLengthValidator(BaseValidator):

    compare = lambda self, a, b: a > b
    clean = lambda self, x: len(x)
    message = 'Ensure this value has length of at most {limit_value} (it has length {show_value}).'
    code = 'max_length'