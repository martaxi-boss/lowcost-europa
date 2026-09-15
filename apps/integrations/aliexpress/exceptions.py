class AliExpressError(Exception):
    """Base exception for AliExpress integration errors."""


class AliExpressConfigurationError(AliExpressError):
    pass


class AliExpressAuthenticationError(AliExpressError):
    pass


class AliExpressTransportError(AliExpressError):
    pass


class AliExpressRateLimitError(AliExpressTransportError):
    pass


class AliExpressAPIError(AliExpressError):
    pass


class AliExpressResponseError(AliExpressError):
    pass
