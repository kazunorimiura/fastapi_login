from fastapi_login.secrets import Secret, SymmetricSecret, AsymmetricSecret
from pydantic import parse_obj_as, ValidationError
import pytest
import secrets

from .conftest import _has_cryptography


parametrize_argvalues = [
    (SymmetricSecret, "HS256", secrets.token_hex(16)),
]
if _has_cryptography:
    from .conftest import generate_rsa_key

    parametrize_argvalues = [
        (SymmetricSecret, "HS256", secrets.token_hex(16)),
        (AsymmetricSecret, "RS256", generate_rsa_key(512).decode()),
        (AsymmetricSecret, "RS256", {"private_key": generate_rsa_key(512)}),
        #
        # Treat rsa-private-key as secret
        (SymmetricSecret, "HS256", generate_rsa_key(512)),
    ]


@pytest.mark.parametrize(("secret_type", "alg", "secret"), parametrize_argvalues)
def test_secret_parsing_happypath(secret_type, alg, secret):
    s = parse_obj_as(Secret, {"algorithms": alg, "secret": secret})
    assert isinstance(s, secret_type)


def test_secret_parsing_case_mismatched_1():
    with pytest.raises(ValidationError, match="Secret is not an asymmetric key."):
        parse_obj_as(Secret, {"algorithms": "RS256", "secret": secrets.token_hex(16)})


def test_secret_parsing_case_mismatched_2():
    with pytest.raises(ValidationError, match="Secret is not an asymmetric key."):
        parse_obj_as(
            Secret,
            {"algorithms": "RS256", "secret": {"private_key": secrets.token_hex(16)}},
        )
