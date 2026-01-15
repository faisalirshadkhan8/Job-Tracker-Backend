"""
Input sanitization utilities for AI prompts.
Protects against prompt injection attacks and cleans user input.
"""

import re
from typing import Optional


class PromptSanitizer:
    """
    Sanitizes user input before sending to LLMs.
    Prevents prompt injection and removes potentially harmful content.
    """

    # Patterns that might indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)",
        r"disregard\s+(all\s+)?(previous|above|prior)",
        r"forget\s+(everything|all|your)\s+(instructions?|rules?|prompts?)",
        r"you\s+are\s+now\s+(a|an)\s+",
        r"act\s+as\s+(a|an|if)",
        r"pretend\s+(to\s+be|you\s+are)",
        r"new\s+instructions?:",
        r"system\s*:\s*",
        r"\[system\]",
        r"\[INST\]",
        r"<\|im_start\|>",
        r"<\|im_end\|>",
    ]

    # Maximum lengths for different input types
    MAX_LENGTHS = {
        "job_description": 10000,
        "resume_text": 15000,
        "company_name": 200,
        "job_title": 200,
        "tone": 50,
        "default": 5000,
    }

    @classmethod
    def sanitize(cls, text: str, field_name: str = "default") -> str:
        """
        Main sanitization method.

        Args:
            text: The input text to sanitize
            field_name: The field name (for length limits)

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Convert to string if needed
        text = str(text)

        # Strip whitespace
        text = text.strip()

        # Enforce length limits
        max_length = cls.MAX_LENGTHS.get(field_name, cls.MAX_LENGTHS["default"])
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Remove null bytes and control characters (except newlines/tabs)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Normalize whitespace (but preserve paragraph breaks)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text

    @classmethod
    def detect_injection(cls, text: str) -> bool:
        """
        Detect potential prompt injection attempts.

        Args:
            text: The input text to check

        Returns:
            True if injection attempt detected
        """
        if not text:
            return False

        text_lower = text.lower()

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    @classmethod
    def sanitize_for_ai(
        cls, text: str, field_name: str = "default", check_injection: bool = True
    ) -> tuple[str, Optional[str]]:
        """
        Full sanitization for AI input.

        Args:
            text: The input text
            field_name: The field name for length limits
            check_injection: Whether to check for injection attempts

        Returns:
            Tuple of (sanitized_text, warning_message)
            warning_message is None if no issues detected
        """
        warning = None

        # Basic sanitization
        sanitized = cls.sanitize(text, field_name)

        # Check for injection attempts
        if check_injection and cls.detect_injection(text):
            warning = "Potentially suspicious content detected and will be processed carefully."

        return sanitized, warning

    @classmethod
    def sanitize_job_description(cls, text: str) -> str:
        """Sanitize job description input."""
        return cls.sanitize(text, "job_description")

    @classmethod
    def sanitize_resume(cls, text: str) -> str:
        """Sanitize resume text input."""
        return cls.sanitize(text, "resume_text")

    @classmethod
    def sanitize_company_name(cls, text: str) -> str:
        """Sanitize company name - more strict."""
        sanitized = cls.sanitize(text, "company_name")
        # Remove any special characters except basic punctuation
        sanitized = re.sub(r"[^\w\s\-\.\,\&\'\"]", "", sanitized)
        return sanitized

    @classmethod
    def sanitize_job_title(cls, text: str) -> str:
        """Sanitize job title - more strict."""
        sanitized = cls.sanitize(text, "job_title")
        # Remove any special characters except basic punctuation
        sanitized = re.sub(r"[^\w\s\-\.\,\(\)\+\#\/]", "", sanitized)
        return sanitized
