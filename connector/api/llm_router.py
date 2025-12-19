"""
LLM Router Module
Routes requests to OpenRouter API (OpenAI-compatible)
"""

from typing import Optional
from dataclasses import dataclass
import httpx
from loguru import logger

from core.config import OpenRouterConfig


@dataclass
class StrategyResult:
    """Strategy generation result"""
    strategy: str
    model_used: str
    tokens_used: int


class LLMRouter:
    """Routes LLM requests to OpenRouter API"""
    
    STRATEGY_SYSTEM_PROMPT = """You are an expert forex trading strategy developer. 
Your task is to analyze market conditions and generate trading strategies.
Always provide clear entry/exit rules, risk management parameters, and specific conditions.
Format your response in a structured way that can be easily parsed and implemented."""
    
    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "HTTP-Referer": "https://nexustrade.id",
                "X-Title": "NexusTrade"
            },
            timeout=60.0
        )
    
    async def generate_strategy(
        self,
        prompt: str,
        symbol: str,
        timeframe: str,
        model: Optional[str] = None
    ) -> StrategyResult:
        """Generate trading strategy using LLM"""
        
        model = model or self.config.default_model
        
        user_prompt = f"""
Symbol: {symbol}
Timeframe: {timeframe}

User Request:
{prompt}

Please generate a complete trading strategy that includes:
1. Entry conditions (specific indicators and values)
2. Exit conditions (take profit and stop loss rules)
3. Position sizing recommendations
4. Risk management rules
5. Best market conditions for this strategy
"""
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.STRATEGY_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            strategy = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            model_used = data.get("model", model)
            
            logger.info(f"Strategy generated using {model_used}, {tokens_used} tokens")
            
            return StrategyResult(
                strategy=strategy,
                model_used=model_used,
                tokens_used=tokens_used
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.text}")
            raise Exception(f"LLM API error: {e.response.status_code}")
        except Exception as e:
            logger.exception(f"Strategy generation failed: {e}")
            raise
    
    async def analyze_market(
        self,
        symbol: str,
        data: dict,
        model: Optional[str] = None
    ) -> str:
        """Analyze market data using LLM"""
        
        model = model or self.config.default_model
        
        prompt = f"""
Analyze the following market data for {symbol}:

Current Price: {data.get('price', 'N/A')}
Daily Change: {data.get('change', 'N/A')}%
Volume: {data.get('volume', 'N/A')}
RSI: {data.get('rsi', 'N/A')}
MACD: {data.get('macd', 'N/A')}

Recent Candles:
{data.get('candles', 'N/A')}

Provide a concise market analysis including:
1. Current trend direction
2. Key support/resistance levels
3. Trading recommendation (buy/sell/hold)
4. Confidence level
"""
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a professional forex analyst. Provide concise, actionable analysis."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 1000
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.exception(f"Market analysis failed: {e}")
            raise
    
    async def chat(
        self,
        message: str,
        history: list = None,
        model: Optional[str] = None
    ) -> str:
        """General chat with LLM"""
        
        model = model or self.config.default_model
        history = history or []
        
        messages = [
            {
                "role": "system",
                "content": "You are NexusTrade AI assistant. Help users with forex trading questions, strategy development, and market analysis."
            }
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1500
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.exception(f"Chat failed: {e}")
            raise
    
    def get_available_models(self) -> list:
        """Get list of recommended models"""
        return [
            "openai/gpt-4-turbo",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "google/gemini-pro",
            "meta-llama/llama-3-70b-instruct"
        ]
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
