import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordStrengthValidator:
    """
    Custom password validator that enforces strong password requirements:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        errors = []
        
        # Length check
        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _("Password must be at least %(min_length)d characters long."),
                    code='password_too_short',
                    params={'min_length': self.min_length},
                )
            )
        
        # Uppercase check
        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one uppercase letter."),
                    code='password_no_upper',
                )
            )
        
        # Lowercase check
        if not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one lowercase letter."),
                    code='password_no_lower',
                )
            )
        
        # Digit check
        if not re.search(r'\d', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one digit."),
                    code='password_no_digit',
                )
            )
        
        # Special character check
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append(
                ValidationError(
                    _("Password must contain at least one special character."),
                    code='password_no_special',
                )
            )
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "Your password must be at least 8 characters long and contain at least one "
            "uppercase letter, one lowercase letter, one digit, and one special character."
        )


def validate_password_strength(password):
    """
    Helper function to validate password strength and return detailed error messages
    """
    validator = PasswordStrengthValidator()
    try:
        validator.validate(password)
        return {'valid': True, 'errors': []}
    except ValidationError as e:
        return {'valid': False, 'errors': [str(error) for error in e.error_list]}
