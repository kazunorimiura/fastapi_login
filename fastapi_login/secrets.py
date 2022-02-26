from pydantic import BaseModel, SecretBytes, Field, validator
from typing import Literal, Annotated, Union

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
except ImportError:
    pass


class RawPrivateSecret(BaseModel):
    private_key: SecretBytes


class AsymmetricSecretIn(BaseModel):
    data: Union[SecretBytes, RawPrivateSecret]

    @property
    def private_key(self):
        if isinstance(self.data, RawPrivateSecret):
            return self.data.private_key.get_secret_value()
        return self.data.get_secret_value()


class AsymmetricPairKey(BaseModel):
    private_key: SecretBytes
    public_key: SecretBytes


class AsymmetricSecret(BaseModel):

    algorithms: Literal["RS256"] = "RS256"
    secret: AsymmetricPairKey

    @validator("secret", pre=True)
    def secret_must_be_asymmetric_private_key(cls, secret):

        secret_in = AsymmetricSecretIn(data=secret)

        try:
            private_key = serialization.load_pem_private_key(
                secret_in.private_key, None, backend=default_backend()
            )
        except Exception as e:
            raise ValueError("Secret is not an asymmetric key.")

        private_key_pem_bytes = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_key_pem_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return AsymmetricPairKey(
            private_key=private_key_pem_bytes, public_key=public_key_pem_bytes
        )

    @property
    def secret_for_decode(self):
        return self.secret.public_key.get_secret_value()

    @property
    def secret_for_encode(self):
        return self.secret.private_key.get_secret_value()


class SymmetricSecret(BaseModel):

    algorithms: Literal["HS256"] = "HS256"
    secret: SecretBytes

    @property
    def secret_for_decode(self):
        return self.secret.get_secret_value()

    @property
    def secret_for_encode(self):
        return self.secret.get_secret_value()


Secret = Annotated[
    Union[SymmetricSecret, AsymmetricSecret], Field(discriminator="algorithms")
]
