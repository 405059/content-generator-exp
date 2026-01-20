import os
from typing import Optional
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage, MessageRole

# ============================================================
# 配置区域 - 请在这里设置您的 API 配置
# Configuration Area - Set your API configuration here
# ============================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")  
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")  
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  
# ============================================================

# Initialize LLM client with environment variables
def _get_llm():
    """
    Initialize and return an OpenAI LLM client configured from top-level variables.
    
    Configuration variables (set at the top of this file):
        OPENAI_API_KEY: Your OpenAI-compatible API key (required)
        OPENAI_API_BASE: Custom API endpoint URL (optional, for custom providers)
        OPENAI_MODEL: Model name to use (optional, defaults to 'gpt-4o')
    
    Returns:
        OpenAI: Configured LLM client
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
    """
    # 从文件顶部的配置变量读取
    api_key = OPENAI_API_KEY
    if not api_key or api_key == "your-api-key-here":
        raise ValueError(
            "请在文件顶部设置 OPENAI_API_KEY！\n"
            "Please set OPENAI_API_KEY at the top of this file!"
        )
    
    api_base = OPENAI_API_BASE
    model = OPENAI_MODEL
    
    # 使用标准 Llama-Index OpenAI 客户端
    if api_base:
        return OpenAI(
            api_key=api_key,
            api_base=api_base,
            model=model,
        )
    else:
        return OpenAI(
            api_key=api_key,
            model=model,
        )


def fix_json_response(response_text: str) -> str:
    """从 LLM 响应中提取纯 JSON,去除 markdown 代码块"""
    import re
    
    # 提取 markdown 代码块中的 JSON
    json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(json_block_pattern, response_text)
    if matches:
        return matches[0].strip()
    
    # 通过大括号/方括号查找 JSON
    json_pattern = r'(\{[\s\S]*\}|\[[\s\S]*\])'
    matches = re.findall(json_pattern, response_text)
    if matches:
        return max(matches, key=len).strip()
    
    return response_text.strip()


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """
    Generate text using a language model API with system and user prompts.

    Args:
        system_prompt (str): System prompt to define the AI's role and behavior.
        user_prompt (str): User input content or question.

    Returns:
        str: Generated text content, or error message if failed.
    
    Note:
        This function uses Llama-Index with OpenAI-compatible API.
        Configure at the top of this file:
        - OPENAI_API_KEY (required)
        - OPENAI_API_BASE (optional, for custom endpoints)
        - OPENAI_MODEL (optional, defaults to 'gpt-4')
    """
    try:
        llm = _get_llm()
        
        # Create chat messages
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=user_prompt),
        ]
        
        # Call LLM and get response
        response = llm.chat(messages)
        
        return response.message.content.strip()
        
    except ValueError as e:
        # Configuration error
        error_msg = f"Configuration error: {e}"
        print(error_msg)
        return f"Error: {e}"
    except Exception as e:
        # Other errors (API errors, network issues, etc.)
        error_msg = f"Text generation failed: {e}"
        print(error_msg)
        return f"Error: {e}"


def generate_image(positive_prompt: str, negative_prompt: str, save_path: str) -> bool:
    """
    Generate an image using a text-to-image model API and save it locally.

    Args:
        positive_prompt (str): Positive prompt describing desired image content.
        negative_prompt (str): Negative prompt describing undesired image content.
        save_path (str): Path to save the image, including filename and extension.

    Returns:
        bool: True if image is successfully generated and saved, False otherwise.
    
    Note:
        TODO: Implement your own image generation API call here (cloud-based or local deployment).
        The function should download/generate the image and save it to save_path.
        
        Llama-Index does not directly support image generation. You can:
        1. Use OpenAI's DALL-E API if your endpoint supports it
        2. Use a separate image generation library (e.g., Stability AI, local Stable Diffusion)
        3. Implement your own custom integration
    """
    
    try:
        # TODO: Implement your image generation API call here
        raise NotImplementedError("Please implement your own image generation API logic")
            
    except Exception as e:
        print(f"Image generation failed: {e}")
        return False