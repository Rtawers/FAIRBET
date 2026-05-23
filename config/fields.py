from django.conf import settings
from django.db import models


class MoneyField(models.DecimalField):
    """DecimalField estandarizado para montos. Precision fija (18, 4). Nunca float.

    Vive en config porque lo comparten wallet, betting y bonos. Si en algun
    momento agregas una app `common/`, este es el primer candidato a mudarse.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_digits", getattr(settings, "MONEY_MAX_DIGITS", 18))
        kwargs.setdefault(
            "decimal_places", getattr(settings, "MONEY_DECIMAL_PLACES", 4)
        )
        super().__init__(*args, **kwargs)
