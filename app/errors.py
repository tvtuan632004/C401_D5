from __future__ import annotations


class AppError(Exception):
    error_category = "system_error"
    error_code = "APP_ERROR"
    status_code = 500

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class UserInputError(AppError):
    error_category = "user_error"
    error_code = "INVALID_INPUT"
    status_code = 400


class EmptyMessageError(UserInputError):
    error_code = "EMPTY_MESSAGE"


class AgentError(AppError):
    error_category = "agent_error"
    error_code = "AGENT_ERROR"
    status_code = 500


class AgentGenerationError(AgentError):
    error_code = "AGENT_GENERATION_FAILED"


class DataError(AppError):
    error_category = "data_error"
    error_code = "DATA_ERROR"
    status_code = 500


class EmptyRetrievalError(DataError):
    error_code = "EMPTY_RETRIEVAL"