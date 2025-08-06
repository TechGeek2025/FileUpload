# image_analyzer.py
"""
Simple base64 image analysis function for frontend integration
"""

import base64
import json
import boto3
from typing import Optional
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_image(
    image_base64: str,
    prompt: Optional[str] = None,
    model_id: Optional[str] = None,
    max_tokens: int = 2000,
    region_name: str = 'us-east-1'
) -> str:
    """
    Analyze image from base64 string and return analysis text
    
    Args:
        image_base64: Base64 encoded image string (with or without data URL prefix)
        prompt: Analysis prompt (optional, uses detailed default)
        model_id: Bedrock model ID (optional, defaults to Claude 3.5 Sonnet)
        max_tokens: Maximum response tokens
        region_name: AWS region for Bedrock
        
    Returns:
        str: Raw analysis text from the vision model
        
    Examples:
        # Basic usage
        analysis = analyze_image(base64_string)
        
        # With custom prompt
        analysis = analyze_image(base64_string, prompt="What do you see?")
        
        # With faster model
        analysis = analyze_image(base64_string, model_id="anthropic.claude-3-5-haiku-20241022-v1:0")
    """
    
    # Default prompt
    if prompt is None:
        prompt = """Analyze this image in detail. Describe:
- All visible objects, people, and their activities
- Setting and environment
- Colors, lighting, and composition
- Any text or signs visible
- Overall mood or atmosphere
- Spatial relationships between elements
Be thorough and objective in your description."""
    
    # Default model
    if model_id is None:
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    try:
        # Initialize Bedrock client
        bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        
        # Clean base64 string (remove data URL prefix if present)
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # Detect image format from base64
        image_format = _detect_image_format(image_base64)
        
        # Prepare message for Claude
        message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{image_format}",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [message],
            "temperature": 0.1
        }
        
        # Call Bedrock
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType='application/json'
        )
        
        # Parse and return response
        response_body = json.loads(response['body'].read())
        analysis = response_body['content'][0]['text']
        
        logger.info(f"Image analysis completed using {model_id}")
        return analysis.strip()
        
    except ClientError as e:
        logger.error(f"AWS Bedrock error: {e}")
        raise Exception(f"Bedrock service error: {str(e)}")
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise Exception(f"Failed to analyze image: {str(e)}")

def _detect_image_format(image_base64: str) -> str:
    """Detect image format from base64 data"""
    try:
        # Decode first few bytes to check format
        image_data = base64.b64decode(image_base64[:100])
        
        if image_data.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'png'
        elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
            return 'gif'
        elif b'WEBP' in image_data[:20]:
            return 'webp'
        else:
            # Default to jpeg
            return 'jpeg'
            
    except Exception:
        # If detection fails, assume jpeg
        return 'jpeg'

# Available models for easy reference
MODELS = {
    'fast': 'anthropic.claude-3-5-haiku-20241022-v1:0',
    'balanced': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'powerful': 'anthropic.claude-3-opus-20240229-v1:0'
}

if __name__ == "__main__":
    print("Base64 Image Analyzer")
    print("Usage: analyze_image(base64_string)")
    print(f"Available models: {list(MODELS.keys())}")
    print("Ready to analyze images from your frontend!")
