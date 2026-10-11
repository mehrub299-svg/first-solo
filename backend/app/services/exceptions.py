class DomainError(Exception):
    """Base class for errors raised by services. The API layer maps these to HTTP."""


class EmailAlreadyRegistered(DomainError):
    pass


class InvalidCredentials(DomainError):
    pass


class InvalidRefreshToken(DomainError):
    pass


class UserNotFound(DomainError):
    pass


class EmbeddingError(DomainError):
    pass


class LLMError(DomainError):
    pass


class EmptyDocument(DomainError):
    pass


class DocumentTooLarge(DomainError):
    pass


class DocumentNotFound(DomainError):
    pass


class ChatNotFound(DomainError):
    pass


class FileTooLarge(DomainError):
    pass


class UnsupportedFileType(DomainError):
    pass


class UnreadableFile(DomainError):
    pass