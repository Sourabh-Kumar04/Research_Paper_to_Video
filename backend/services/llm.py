"""
LLM service integration for the RASO platform.

Provides unified interface for multiple LLM providers including local (Ollama)
and cloud-based services (OpenAI, Anthropic, Google) with fallback mechanisms.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum

import aiohttp
import openai
import anthropic
from pydantic import BaseModel, Field

from backend.config import get_config
from agents.retry import retry, RetryConfig
from agents.logging import AgentLogger


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMResponse(BaseModel):
    """Response from LLM service."""
    
    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model used for generation")
    provider: LLMProvider = Field(..., description="Provider used")
    
    # Usage statistics
    prompt_tokens: Optional[int] = Field(default=None, description="Number of prompt tokens")
    completion_tokens: Optional[int] = Field(default=None, description="Number of completion tokens")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens used")
    
    # Timing information
    response_time: float = Field(..., description="Response time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score")
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Calculate tokens per second generation rate."""
        if self.completion_tokens and self.response_time > 0:
            return self.completion_tokens / self.response_time
        return None


class LLMRequest(BaseModel):
    """Request to LLM service."""
    
    prompt: str = Field(..., description="Input prompt")
    model: Optional[str] = Field(default=None, description="Specific model to use")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Sampling temperature")
    
    # Advanced parameters
    system_prompt: Optional[str] = Field(default=None, description="System prompt for context")
    stop_sequences: Optional[List[str]] = Field(default=None, description="Stop generation sequences")
    
    # Metadata
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, provider_type: LLMProvider):
        """Initialize the provider."""
        self.provider_type = provider_type
        self.config = get_config()
        self.logger = AgentLogger(None)  # Will be set by service
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using the LLM.
        
        Args:
            request: LLM request parameters
            
        Returns:
            LLM response with generated content
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is available.
        
        Returns:
            True if provider is available
        """
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """
        Get list of available models.
        
        Returns:
            List of model names
        """
        pass
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session if needed."""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=self.config.llm.timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _validate_request(self, request: LLMRequest) -> None:
        """Validate LLM request."""
        if not request.prompt or not request.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if request.max_tokens and request.max_tokens > self.config.llm.max_tokens:
            raise ValueError(f"Max tokens exceeds limit: {self.config.llm.max_tokens}")


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self):
        """Initialize Ollama provider."""
        super().__init__(LLMProvider.OLLAMA)
    
    @property
    def name(self) -> str:
        return "Ollama"
    
    @property
    def default_model(self) -> str:
        return self.config.llm.ollama_model
    
    @retry(max_attempts=3, base_delay=1.0)
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Ollama."""
        self._validate_request(request)
        
        start_time = time.time()
        session = await self._create_session()
        
        # Prepare request payload
        payload = {
            "model": request.model or self.default_model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature or self.config.llm.temperature,
            }
        }
        
        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens
        
        if request.system_prompt:
            payload["system"] = request.system_prompt
        
        if request.stop_sequences:
            payload["options"]["stop"] = request.stop_sequences
        
        try:
            url = f"{self.config.llm.ollama_url}/api/generate"
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama API error {response.status}: {error_text}")
                
                result = await response.json()
                
                response_time = time.time() - start_time
                
                return LLMResponse(
                    content=result.get("response", ""),
                    model=payload["model"],
                    provider=self.provider_type,
                    prompt_tokens=result.get("prompt_eval_count"),
                    completion_tokens=result.get("eval_count"),
                    total_tokens=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                    response_time=response_time,
                )
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Ollama connection error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            session = await self._create_session()
            url = f"{self.config.llm.ollama_url}/api/tags"
            
            async with session.get(url) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get available Ollama models."""
        try:
            session = await self._create_session()
            url = f"{self.config.llm.ollama_url}/api/tags"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
                
        except Exception:
            pass
        
        return []


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self):
        """Initialize OpenAI provider."""
        super().__init__(LLMProvider.OPENAI)
        self._client: Optional[openai.AsyncOpenAI] = None
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def default_model(self) -> str:
        return self.config.llm.openai_model
    
    def _get_client(self) -> openai.AsyncOpenAI:
        """Get OpenAI client."""
        if not self._client:
            if not self.config.llm.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            self._client = openai.AsyncOpenAI(
                api_key=self.config.llm.openai_api_key,
                timeout=self.config.llm.timeout_seconds,
            )
        
        return self._client
    
    @retry(max_attempts=3, base_delay=2.0)
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using OpenAI."""
        self._validate_request(request)
        
        start_time = time.time()
        client = self._get_client()
        
        # Prepare messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        
        messages.append({"role": "user", "content": request.prompt})
        
        # Prepare parameters
        params = {
            "model": request.model or self.default_model,
            "messages": messages,
            "temperature": request.temperature or self.config.llm.temperature,
        }
        
        if request.max_tokens:
            params["max_tokens"] = request.max_tokens
        
        if request.stop_sequences:
            params["stop"] = request.stop_sequences
        
        try:
            response = await client.chat.completions.create(**params)
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider=self.provider_type,
                prompt_tokens=response.usage.prompt_tokens if response.usage else None,
                completion_tokens=response.usage.completion_tokens if response.usage else None,
                total_tokens=response.usage.total_tokens if response.usage else None,
                response_time=response_time,
            )
            
        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if OpenAI is available."""
        if not self.config.llm.openai_api_key:
            return False
        
        try:
            client = self._get_client()
            # Try a minimal request to check availability
            await client.models.list()
            return True
            
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get available OpenAI models."""
        try:
            client = self._get_client()
            models = await client.models.list()
            return [model.id for model in models.data if "gpt" in model.id]
            
        except Exception:
            return []


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self):
        """Initialize Anthropic provider."""
        super().__init__(LLMProvider.ANTHROPIC)
        self._client: Optional[anthropic.AsyncAnthropic] = None
    
    @property
    def name(self) -> str:
        return "Anthropic"
    
    @property
    def default_model(self) -> str:
        return self.config.llm.anthropic_model
    
    def _get_client(self) -> anthropic.AsyncAnthropic:
        """Get Anthropic client."""
        if not self._client:
            if not self.config.llm.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            
            self._client = anthropic.AsyncAnthropic(
                api_key=self.config.llm.anthropic_api_key,
                timeout=self.config.llm.timeout_seconds,
            )
        
        return self._client
    
    @retry(max_attempts=3, base_delay=2.0)
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Anthropic Claude."""
        self._validate_request(request)
        
        start_time = time.time()
        client = self._get_client()
        
        # Prepare parameters
        params = {
            "model": request.model or self.default_model,
            "max_tokens": request.max_tokens or 1000,
            "temperature": request.temperature or self.config.llm.temperature,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        
        if request.system_prompt:
            params["system"] = request.system_prompt
        
        if request.stop_sequences:
            params["stop_sequences"] = request.stop_sequences
        
        try:
            response = await client.messages.create(**params)
            
            response_time = time.time() - start_time
            
            # Extract content from response
            content = ""
            if response.content:
                content = response.content[0].text if response.content else ""
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_type,
                prompt_tokens=response.usage.input_tokens if response.usage else None,
                completion_tokens=response.usage.output_tokens if response.usage else None,
                total_tokens=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else None,
                response_time=response_time,
            )
            
        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if Anthropic is available."""
        if not self.config.llm.anthropic_api_key:
            return False
        
        try:
            # Anthropic doesn't have a simple health check, so we'll assume it's available
            # if we have an API key
            return True
            
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        # Anthropic doesn't provide a models endpoint, return known models
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
        ]


class GoogleProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""
    
    def __init__(self):
        """Initialize Google provider."""
        super().__init__(LLMProvider.GOOGLE)
    
    @property
    def name(self) -> str:
        return "Google"
    
    @property
    def default_model(self) -> str:
        return self.config.llm.google_model
    
    @retry(max_attempts=3, base_delay=2.0)
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Google Gemini."""
        self._validate_request(request)
        
        if not self.config.llm.google_api_key:
            raise ValueError("Google API key not configured")
        
        start_time = time.time()
        session = await self._create_session()
        
        # Prepare request payload
        model = request.model or self.default_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": request.prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": request.temperature or self.config.llm.temperature,
            }
        }
        
        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
        
        if request.stop_sequences:
            payload["generationConfig"]["stopSequences"] = request.stop_sequences
        
        headers = {
            "Content-Type": "application/json",
        }
        
        params = {
            "key": self.config.llm.google_api_key
        }
        
        try:
            async with session.post(url, json=payload, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RuntimeError(f"Google API error {response.status}: {error_text}")
                
                result = await response.json()
                
                response_time = time.time() - start_time
                
                # Extract content
                content = ""
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            content = parts[0]["text"]
                
                # Extract usage info if available
                usage_metadata = result.get("usageMetadata", {})
                
                return LLMResponse(
                    content=content,
                    model=model,
                    provider=self.provider_type,
                    prompt_tokens=usage_metadata.get("promptTokenCount"),
                    completion_tokens=usage_metadata.get("candidatesTokenCount"),
                    total_tokens=usage_metadata.get("totalTokenCount"),
                    response_time=response_time,
                )
                
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Google API connection error: {str(e)}")
    
    async def is_available(self) -> bool:
        """Check if Google Gemini is available."""
        if not self.config.llm.google_api_key:
            return False
        
        try:
            session = await self._create_session()
            url = "https://generativelanguage.googleapis.com/v1beta/models"
            params = {"key": self.config.llm.google_api_key}
            
            async with session.get(url, params=params) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get available Google models."""
        try:
            session = await self._create_session()
            url = "https://generativelanguage.googleapis.com/v1beta/models"
            params = {"key": self.config.llm.google_api_key}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("models", []):
                        name = model.get("name", "")
                        if "gemini" in name.lower():
                            # Extract model name from full path
                            model_id = name.split("/")[-1]
                            models.append(model_id)
                    return models
                
        except Exception:
            pass
        
        return ["gemini-pro", "gemini-pro-vision"]


class LLMService:
    """Unified LLM service with multiple provider support and fallback."""
    
    def __init__(self):
        """Initialize LLM service."""
        self.config = get_config()
        self.logger = AgentLogger(None)
        
        # Initialize providers
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {
            LLMProvider.OLLAMA: OllamaProvider(),
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.ANTHROPIC: AnthropicProvider(),
            LLMProvider.GOOGLE: GoogleProvider(),
        }
        
        # Set logger for all providers
        for provider in self.providers.values():
            provider.logger = self.logger
        
        # Provider priority order (local first)
        self.provider_priority = [
            LLMProvider.OLLAMA,
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.GOOGLE,
        ]
    
    async def generate(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using the best available provider.
        
        Args:
            prompt: Input prompt
            model: Specific model to use
            provider: Specific provider to use
            **kwargs: Additional parameters
            
        Returns:
            LLM response
        """
        request = LLMRequest(
            prompt=prompt,
            model=model,
            **kwargs
        )
        
        # If specific provider requested, use it
        if provider:
            return await self._generate_with_provider(provider, request)
        
        # Otherwise, try providers in priority order
        last_error = None
        
        for provider_type in self.provider_priority:
            try:
                # Check if provider is available
                provider_instance = self.providers[provider_type]
                if not await provider_instance.is_available():
                    self.logger.debug(f"Provider {provider_type} not available, skipping")
                    continue
                
                # Try generation
                response = await self._generate_with_provider(provider_type, request)
                
                self.logger.info(
                    f"Successfully generated text using {provider_type}",
                    model=response.model,
                    tokens=response.total_tokens,
                    response_time=response.response_time,
                )
                
                return response
                
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Provider {provider_type} failed: {str(e)}",
                    exception=e
                )
                continue
        
        # All providers failed
        raise RuntimeError(f"All LLM providers failed. Last error: {str(last_error)}")
    
    async def _generate_with_provider(
        self, 
        provider_type: LLMProvider, 
        request: LLMRequest
    ) -> LLMResponse:
        """Generate text with specific provider."""
        provider = self.providers[provider_type]
        
        # Use provider's default model if none specified
        if not request.model:
            request.model = provider.default_model
        
        return await provider.generate(request)
    
    async def get_available_providers(self) -> List[LLMProvider]:
        """Get list of available providers."""
        available = []
        
        for provider_type, provider in self.providers.items():
            try:
                if await provider.is_available():
                    available.append(provider_type)
            except Exception:
                pass
        
        return available
    
    async def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """Get available models for a provider."""
        if provider not in self.providers:
            return []
        
        try:
            return await self.providers[provider].get_available_models()
        except Exception:
            return []
    
    async def validate_response(self, response: LLMResponse, schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate LLM response against schema.
        
        Args:
            response: LLM response to validate
            schema: Optional JSON schema for validation
            
        Returns:
            True if valid
        """
        # Basic validation
        if not response.content or not response.content.strip():
            return False
        
        # Schema validation if provided
        if schema:
            try:
                import jsonschema
                # Try to parse response as JSON if schema provided
                content_json = json.loads(response.content)
                jsonschema.validate(content_json, schema)
                return True
            except (json.JSONDecodeError, jsonschema.ValidationError):
                return False
        
        return True
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        for provider in self.providers.values():
            try:
                await provider._close_session()
            except Exception:
                pass


# Global LLM service instance
llm_service = LLMService()