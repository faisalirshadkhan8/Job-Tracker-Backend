"""
Groq AI Service for LLM-powered features.
Handles all interactions with Groq API.
"""

import time
from typing import Optional, TYPE_CHECKING
from django.conf import settings

if TYPE_CHECKING:
    from groq import Groq

try:
    from groq import Groq
except ImportError:
    Groq = None


class GroqService:
    """
    Service class for Groq AI operations.
    Provides a reusable interface for LLM calls with retry logic.
    """
    
    _client = None
    
    @classmethod
    def get_client(cls) -> 'Groq | None':
        """Get or create Groq client singleton."""
        if Groq is None:
            raise ImportError("groq package is not installed. Run: pip install groq")
        
        if cls._client is None:
            api_key = getattr(settings, 'GROQ_API_KEY', None)
            if not api_key:
                raise ValueError("GROQ_API_KEY is not configured in settings")
            cls._client = Groq(api_key=api_key)
        return cls._client
    
    @classmethod
    def get_model(cls) -> str:
        """Get the configured AI model."""
        model = getattr(settings, 'AI_MODEL', 'groq/llama-3.3-70b-versatile')
        # Remove 'groq/' prefix if present
        if model.startswith('groq/'):
            model = model[5:]
        return model
    
    @classmethod
    def generate_text(
        cls,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        retry_count: int = 3,
        retry_delay: float = 1.0
    ) -> dict:
        """
        Generate text using Groq LLM.
        
        Args:
            prompt: The user prompt/question
            system_prompt: Optional system instructions
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum response length
            retry_count: Number of retries on failure
            retry_delay: Delay between retries in seconds
            
        Returns:
            dict with 'content', 'model', 'usage' keys
        """
        client = cls.get_client()
        model = cls.get_model()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        last_error = None
        for attempt in range(retry_count):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                return {
                    'content': response.choices[0].message.content,
                    'model': model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    },
                    'finish_reason': response.choices[0].finish_reason
                }
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                continue
        
        raise Exception(f"Groq API call failed after {retry_count} attempts: {str(last_error)}")
    
    @classmethod
    def generate_cover_letter(
        cls,
        job_description: str,
        resume_text: str,
        company_name: str,
        job_title: str,
        tone: str = "professional"
    ) -> dict:
        """
        Generate a personalized cover letter.
        
        Args:
            job_description: The job posting text
            resume_text: The candidate's resume text
            company_name: Name of the company
            job_title: Title of the position
            tone: Writing tone (professional, enthusiastic, formal)
            
        Returns:
            dict with 'cover_letter', 'key_points', 'model', 'usage'
        """
        from .prompts import COVER_LETTER_SYSTEM_PROMPT, COVER_LETTER_USER_PROMPT
        
        system_prompt = COVER_LETTER_SYSTEM_PROMPT.format(tone=tone)
        user_prompt = COVER_LETTER_USER_PROMPT.format(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            resume_text=resume_text
        )
        
        result = cls.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1500
        )
        
        return {
            'cover_letter': result['content'],
            'model': result['model'],
            'usage': result['usage']
        }
    
    @classmethod
    def analyze_job_match(
        cls,
        job_description: str,
        resume_text: str
    ) -> dict:
        """
        Analyze how well a resume matches a job description.
        
        Returns:
            dict with 'score', 'matching_skills', 'missing_skills', 'recommendations'
        """
        from .prompts import JOB_MATCH_SYSTEM_PROMPT, JOB_MATCH_USER_PROMPT
        
        user_prompt = JOB_MATCH_USER_PROMPT.format(
            job_description=job_description,
            resume_text=resume_text
        )
        
        result = cls.generate_text(
            prompt=user_prompt,
            system_prompt=JOB_MATCH_SYSTEM_PROMPT,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=1000
        )
        
        return {
            'analysis': result['content'],
            'model': result['model'],
            'usage': result['usage']
        }
    
    @classmethod
    def generate_interview_questions(
        cls,
        job_description: str,
        company_name: str,
        job_title: str,
        question_count: int = 10
    ) -> dict:
        """
        Generate likely interview questions for a position.
        
        Returns:
            dict with 'questions', 'model', 'usage'
        """
        from .prompts import INTERVIEW_QUESTIONS_SYSTEM_PROMPT, INTERVIEW_QUESTIONS_USER_PROMPT
        
        user_prompt = INTERVIEW_QUESTIONS_USER_PROMPT.format(
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            question_count=question_count
        )
        
        result = cls.generate_text(
            prompt=user_prompt,
            system_prompt=INTERVIEW_QUESTIONS_SYSTEM_PROMPT,
            temperature=0.6,
            max_tokens=1500
        )
        
        return {
            'questions': result['content'],
            'model': result['model'],
            'usage': result['usage']
        }
