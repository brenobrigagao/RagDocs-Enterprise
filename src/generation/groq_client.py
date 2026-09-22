import logging
from typing import Any

from groq import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from langchain_groq import ChatGroq
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

TRANSIENT_ERRROS = (
    RateLimitError,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
)

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
        retry=retry_if_exception_type(TRANSIENT_ERRROS),
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

    try:
        llm = _build_llm(settings.groq_model_primary)
        answer = _call_with_retry(llm, SYSTEM_PROMPT, user_prompt)
        return answer, settings.groq_model_primary
    except RateLimitError:
        logger.warning(
            "Rate limit exhausted for the primary model (%s) even after retries; "
            "using fallback (%s).",
            settings.groq_model_primary,
            settings.groq_model_fallback,
        )
        llm = _build_llm(settings.groq_model_fallback)
        answer = _call_with_retry(llm, SYSTEM_PROMPT, user_prompt)
        return answer, settings.groq_model_fallback