import re

from django.core.exceptions import ValidationError


class UppercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall("[A-Z]", password):
            raise ValidationError(
                "The password must contain at least 1 uppercase letter, A-Z.",
                code="password_no_upper",
            )

    def get_help_text(self):
        return "Your password must contain at least 1 uppercase letter, A-Z."


class LowercaseValidator(object):
    def validate(self, password, user=None):
        if not re.findall("[a-z]", password):
            raise ValidationError(
                "The password must contain at least 1 uppercase letter, a-z.",
                code="password_no_upper",
            )

    def get_help_text(self):
        return "Your password must contain at least 1 uppercase letter, a-z."


class SpecialCharValidator(object):

    """
    The password must contain at least 1 special character @#$%!^&*
    """

    def validate(self, password, user=None):
        if not re.findall("[@#$%!^&*()]", password):
            raise ValidationError(
                (
                    "The password must contain at least 1 special character: @#$%!^&*()"
                ),
                code="password_no_symbol",
            )

    def get_help_text(self):
        return "Your password must contain at least 1 special character: @#$%!^&*()"


class NumberValidator(object):

    """
    The password must contain at least 1 Number
    """

    def validate(self, password, user=None):
        if not re.findall("[0-9]", password):
            raise ValidationError(
                "The password must contain at least 1 Number",
                code="password_no_symbol",
            )

    def get_help_text(self):
        return "Your password must contain at least 1 Number "
