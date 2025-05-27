import os
import json
from dataclasses import asdict, dataclass
from typing import List, Union, Optional
from photo_service import search_photos
from openai import OpenAI
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryPayload:
    search_query: str
    
    def to_dict(self):
        return {"search_query": self.search_query}


@dataclass
class ResponsePayload:
    message: str
    photo_ids: List[int]
    
    def to_dict(self):
        return {"message": self.message, "photo_ids": self.photo_ids}


@dataclass
class LLMResponse:
    type: str
    payload: Union[QueryPayload, ResponsePayload]
    
    def to_dict(self):
        return {
            "type": self.type,
            "payload": self.payload.to_dict()
        }
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LLMResponse':
        """
        Parse JSON string into LLMResponse dataclass
        
        Args:
            json_str (str): JSON string from LLM
            
        Returns:
            LLMResponse: Parsed response object
            
        Raises:
            ValueError: If JSON is invalid or has unexpected structure
        """
        try:
            data = json.loads(json_str)
            
            if not isinstance(data, dict) or 'type' not in data or 'payload' not in data:
                raise ValueError("Invalid response structure: missing 'type' or 'payload'")
            
            response_type = data['type']
            payload_data = data['payload']
            
            payload: Union[QueryPayload, ResponsePayload]
            
            if response_type == "query":
                if 'search_query' not in payload_data:
                    raise ValueError("Query payload missing 'search_query'")
                payload = QueryPayload(search_query=payload_data['search_query'])
                
            elif response_type == "response":
                if 'message' not in payload_data or 'photo_ids' not in payload_data:
                    raise ValueError("Response payload missing 'message' or 'photo_ids'")
                
                # Ensure photo_ids is a list of integers
                photo_ids = payload_data['photo_ids']
                if not isinstance(photo_ids, list):
                    raise ValueError("photo_ids must be a list")
                
                # Convert to integers and validate
                try:
                    photo_ids = [int(id) for id in photo_ids]
                except (ValueError, TypeError):
                    raise ValueError("All photo_ids must be integers")
                
                payload = ResponsePayload(
                    message=payload_data['message'],
                    photo_ids=photo_ids
                )
                
            else:
                raise ValueError(f"Unknown response type: {response_type}")
            
            return cls(type=response_type, payload=payload)
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def is_query(self) -> bool:
        """Check if this is a query response"""
        return self.type == "query"
    
    def is_response(self) -> bool:
        """Check if this is a final response"""
        return self.type == "response"
    
    def get_search_query(self) -> Optional[str]:
        """Get search query if this is a query response"""
        if self.is_query() and isinstance(self.payload, QueryPayload):
            return self.payload.search_query
        return None
    
    def get_message(self) -> Optional[str]:
        """Get message if this is a response"""
        if self.is_response() and isinstance(self.payload, ResponsePayload):
            return self.payload.message
        return None
    
    def get_photo_ids(self) -> List[int]:
        """Get photo IDs if this is a response"""
        if self.is_response() and isinstance(self.payload, ResponsePayload):
            return self.payload.photo_ids
        return []


@dataclass
class ImageInput:
    image_url: str
    type: str = "input_image"
    
    def to_dict(self):
        return {"type": self.type, "image_url": self.image_url}

@dataclass
class TextInput:
    text: str
    type: str = "input_text"
    
    def to_dict(self):
        return {"type": self.type, "text": self.text}

@dataclass
class TextOutput:
    text: str
    type: str = "output_text"
    
    def to_dict(self):
        return {"type": self.type, "text": self.text}


@dataclass
class Message:
    role: str
    content: list[ImageInput | TextInput]
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": [item.to_dict() for item in self.content]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create Message from dictionary"""
        content_items: list[ImageInput | TextInput] = []
        for item in data.get("content", []):
            if item.get("type") == "input_text":
                content_items.append(TextInput(text=item["text"]))
            elif item.get("type") == "input_image":
                content_items.append(ImageInput(image_url=item["image_url"]))
        
        return cls(role=data["role"], content=content_items)



# Initialize the OpenAI client
# The API key should be set in the environment variable OPENAI_API_KEY
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def chat(messages: list[Message]) -> Optional[LLMResponse]:
    """
    Simple chat function that takes a single prompt and returns the parsed response
    
    Args:
        prompt (str): The user's prompt
        model (str): The model to use
    
    Returns:
        LLMResponse: Parsed response object, or None if error occurred
    """
    messages = [
        Message(role="system", content=[TextInput(type="input_text", text="""You are an AI assistant that has access to the user's photo collection and can answer questions about them. Your goal is to provide helpful, accurate responses about the user's photos and life experiences captured in those images.

RESPONSE FORMATS:
You must respond in one of two JSON formats depending on whether you need additional photo context:

1. QUERY FORMAT - Use when you need to see photos to answer the question:
{
    "type": "query",
    "payload": {
        "search_query": "specific search terms"
    }
}

2. RESPONSE FORMAT - Use when you can answer without additional photos or when providing a final answer:
{
    "type": "response",
    "payload": {
        "message": "Your detailed response here",
        "photo_ids": [list of relevant photo IDs, or empty array if none]
    }
}

WHEN TO QUERY vs RESPOND:
- QUERY when: The user asks about specific objects, people, places, or events that would require seeing photos to answer accurately
- QUERY when: You need visual confirmation or additional context from photos
- RESPOND when: You can answer based on general knowledge or previous photo context provided
- RESPOND when: The user asks general questions that don't require specific photo analysis

QUERY GUIDELINES:
- Use specific, descriptive search terms (e.g., "dogs", "vacation beach", "birthday cake", "family dinner")
- Be concise but descriptive enough to find relevant photos
- Focus on key visual elements or concepts the user is asking about

RESPONSE GUIDELINES:
- Provide helpful, detailed answers based on the available information
- Reference specific photos by their IDs when relevant
- Be conversational and engaging
- If you mention photos in your response, always include their IDs in the photo_ids array

IMPORTANT: Always respond with valid JSON in one of the two formats above. Do not include any text outside the JSON structure.""")]),
        *messages,
    ]

    
    response = None
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[asdict(message) for message in messages],
            # temperature=0.3
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")

    
    if response and response.output_text:
        try:
            raw_response = response.output_text
            return LLMResponse.from_json(raw_response)
        except ValueError as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Raw response: {response.output_text}")
            return None
    else:
        logger.error("No response received from OpenAI API")
        return None


def run_chat(messages: list[Message]):
    response = chat(messages)
    while response and response.is_query():
        # Add the previous response to the messages
        # messages.append(Message(role="assistant", content=response.get_message()))
        # Get the search query
        search_query = response.get_search_query()
        logger.info(f"Query: {search_query}")
        assert search_query is not None
        # Get the photos
        photos = search_photos(search_query)
        for photo in photos:
            messages.append(Message(role="user", content=[TextInput(text=f"Here is a photo that was taken in {photo.location} on {photo.timestamp}"), ImageInput(image_url=f"data:image/png;base64,{photo.data}")]))
        response = chat(messages)

    return response


# Example usage:
if __name__ == "__main__":
    # Make sure to set your OPENAI_API_KEY environment variable
    from main import create_app
    app = create_app()
    with app.app_context():
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("Please set the OPENAI_API_KEY environment variable")
        else:
            # Example chat
            response = run_chat([Message(role="user", content=[TextInput(text="When did I go to the forest?")])])
            if response:
                logger.info(f"Response type: {response.type}")
                logger.info(f"Message: {response.get_message()}")
                logger.info(f"Photo IDs: {response.get_photo_ids()}")
                logger.info(f"Search query: {response.get_search_query()}") 