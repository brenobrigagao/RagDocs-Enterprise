import logging
from groq import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from langchain_groq import ChatGroq
from groq import NotFoundError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings
from src.generation.config import get_generation_config
from src.generation.prompts.v1_qa_prompt import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    format_context,
)

logger = logging.getLogger(__name__)

TRANSIENT_ERRORS = (
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
)
FALLBACK_ERRORS = TRANSIENT_ERRORS + (NotFoundError,)

def _build_llm(model_name: str) -> ChatGroq:
    config = get_generation_config()
    return ChatGroq(
        model=model_name,
        api_key=settings.groq_api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

def _call_with_retry(
        llm: ChatGroq, system_prompt: str, user_prompt: str, max_retries: int
) -> str:
    @retry(
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(max_retries),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _invoke() -> str:
        response = llm.invoke(
            [("system", system_prompt), ("human", user_prompt)]
        )
        return str(response.content)

    return _invoke()

def generate_answer(question: str, sources: list) -> tuple[str, str]:
    context = format_context(sources)
    user_prompt = USER_PROMPT_TEMPLATE.format(context=context, question=question)
    config = get_generation_config()

    try:
        llm = _build_llm(settings.groq_model_primary)
        answer = _call_with_retry(
            llm, SYSTEM_PROMPT, user_prompt, max_retries=config.max_retries
        )
        return answer, settings.groq_model_primary
    except FALLBACK_ERRORS as exc:
        logger.warning(
            "Primary model (%s) failed after retries (%s); using fallback (%s).",
            settings.groq_model_primary,
            exc,
            settings.groq_model_fallback,
        )
        llm_fallback = _build_llm(settings.groq_model_fallback)
        answer = _call_with_retry(
            llm_fallback, SYSTEM_PROMPT, user_prompt, max_retries=config.max_retries
        )
        return answer, settings.groq_model_fallback