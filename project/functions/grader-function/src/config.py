import environ


@environ.config(prefix="APP")
class AppConfig:
    environment = environ.var(help="This is the environment.", default="dev")


@environ.config(prefix="BOTO_SESSION")
class BotoSessionConfig:
    endpoint = environ.var(help="This is the endpoint.")
    role_alias = environ.var(help="This is the role alias.")
    certificate = environ.var(help="This is the certificate.")
    private_key = environ.var(help="This is the private key.")
    thing_name = environ.var(help="This is the thing name.")


@environ.config(prefix="PARAMETER_STORE")
class ParameterStoreConfig:
    secret_name = environ.var(help="This is the secret name.")
