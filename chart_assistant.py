import asyncio
import os
import traceback
import base64
import io
from config import Config
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.core.exceptions import HttpResponseError
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Tuple, Dict, Any, Optional, Union

SYSTEM_PROMPT = """You are a chart analysis expert. 
    Analyze charts and provide:
    1. Chart type
    2. Key data points
    3. Trends and insights
    4. Concise summary"""
    
class ChartsAssistant: 
    def __init__(self):
        Config.validate_env_variables()
        self.openai_client = Config.get_openai_client()
        self.vision_client = Config.get_vision_client()
   
async def analyze_chart(self, files: List[Tuple[str, bytes]]) -> str:
    """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data.
    Args:
        files (List[Tuple[str, bytes]]): List of tuples containing filename and image data in bytes.
    Returns: str: The analysis result from GPT-4 Vision.
    """
    try:
        if not files:
            print("No files provided to analyze_chart.")
            return ""

        # Limitujemy liczbę plików do przetworzenia
        total_files = len(files)
        if total_files > MAX_FILES_TO_PROCESS:
            print(f"Warning: Processing limited to {MAX_FILES_TO_PROCESS} files out of {total_files} uploaded.")
        files_to_process = files[:MAX_FILES_TO_PROCESS]

        image_bytes_dict = {}
        base64_images_dict = {}
        all_text_results = []

        # Przygotowujemy tylko te pliki, które zamierzamy przetworzyć
        for filename, image_data in files_to_process:
            if isinstance(image_data, bytes):
                image_bytes_dict[filename] = image_data
                base64_images_dict[filename] = base64.b64encode(image_data).decode('utf-8')
            else:
                # Already base64
                image_bytes_dict[filename] = base64.b64decode(image_data)
                base64_images_dict[filename] = image_data

        # Read operation for OCR from file
        print("Extracting text with OCR...")

        # Process in parallel (tylko ograniczona lista)
        tasks = [self.process_single_file(fn, data) for fn, data in files_to_process]
        all_text_results = await asyncio.gather(*tasks)

        print("Analyzing with GPT-4 Vision...")

        ocr_summary = "\n\n".join([f"**{filename}:**\n{text}" for filename, text in all_text_results])

        user_prompt = [
                {
                    "type": "text",
                    "text": f"""Analyze these charts:
            OCR Data:
            {ocr_summary[:500]}
            Return structured analysis."""
                }
            ]

        # Upewniamy się, że iterujemy po wynikach a nie po oryginalnych wpisach
        for filename, _ in all_text_results:
            # zabezpieczenie: jeśli brakuje base64 dla pliku, pomijamy go
            if filename in base64_images_dict:
                user_prompt.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_images_dict[filename]}"
                    }
                })
            else:
                print(f"Warning: missing base64 data for {filename}, skipping image attachment to prompt.")

        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            max_tokens=2500,
            temperature=0.3
        )

        print(f"Response received: {response.choices[0].message.content[:200]}")
        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ ERROR in analyze_chart: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        raise

    

    @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10)
        )
    async def process_single_file(self, filename: str, image_bytes: bytes) -> Tuple[str, str]:
        """Process a single file with OCR
        Args:
            filename (str): The name of the file.
            image_bytes (bytes): The image data in bytes.
        Returns: Tuple[str, str]: The filename and extracted text.
        """
        try:
            print(f"Processing {filename}...")
            image_stream = io.BytesIO(image_bytes)
            image_stream.seek(0)
            
            try:
                # read_result = self.vision_client.read_in_stream(image_stream, raw=True)
                loop = asyncio.get_event_loop()
                read_result = await loop.run_in_executor(
                    None,  # Uses default ThreadPoolExecutor
                    lambda: self.vision_client.read_in_stream(image_stream, raw=True)
                )
            except HttpResponseError as e:
                if e.status_code == 429:
                    print(f"Rate limit exceeded, retrying...")
                    raise
                elif e.status_code == 400:
                    print(f"Invalid image format: {e}")
                    return (filename, "")
                elif e.status_code == 500:
                    print(f"Server error, retrying...")
                    raise
                else:
                    raise
            operation_id = read_result.headers["Operation-Location"].split("/")[-1]
            
            print(f"Operation ID for {filename}: {operation_id}")
            
            result = await self._poll_for_result(operation_id)
            
            if result is None:
                print(f"Failed to get result for {filename}")
                return (filename, "")
            
            extracted = self.extract_text(result)
            print(f"Extracted text from {filename}: {len(extracted)} characters")
            
            return (filename, extracted)
            
        except Exception as e:
            print(f"Error processing {filename}")
            return (filename, "")

    def extract_text(self, result: Optional[Union[Dict[str, Any], Any]]) -> str:
        """Extract text from OCR result
        Args:
            result (Optional[Union[Dict[str, Any], Any]]): The read result.
        Returns: str: Extracted text.
        """
        if result is None:
            return ""
        analyze_result = result.get('analyze_result') if isinstance(result, dict) else result.analyze_result
        file_text_items = []
        if analyze_result and hasattr(analyze_result, 'read_results'):
            for page in analyze_result.read_results:
                for line in page.lines:
                    file_text_items.append({
                        'text': line.text,
                        'bbox': line.bounding_box
                    })
        extracted_text = "\n".join([item['text'] for item in file_text_items])
        return extracted_text
    
    
    async def _poll_for_result(self, operation_id: str, max_attempts: int = 30, poll_interval: int = 1) -> Optional[Union[Dict[str, Any], Any]]:
        """Poll for Read operation result
        Args:
            operation_id (str): The operation ID to poll.
            max_attempts (int): Maximum number of polling attempts.
            poll_interval (int): Time in seconds between polling attempts.
        Returns: Optional[Union[Dict[str, Any], Any]]: The read result or None if failed.
        """
        print("   Polling for results...", end="", flush=True)
        
        for attempt in range(max_attempts):
            try:
                # Use the vision client created in __init__ to get the read result
                result = self.vision_client.get_read_result(operation_id)

                if result.status == OperationStatusCodes.succeeded:
                    print(" ✓ Succeeded")
                    return result
                elif result.status == OperationStatusCodes.failed:
                    print(" ✗ Failed")
                    return None
                
                print(".", end="", flush=True)
                await asyncio.sleep(poll_interval)
            except Exception as e:
                print(f" ✗ Error polling")
                return None
        
        print(" ✗ Timeout")
        return None

    def followup_response(self, question: str, previous_analysis: str) -> str:
        """Generate follow-up response based on previous analysis.
        Args:
            question (str): The follow-up question.
            previous_analysis (str): The previous chart analysis.
        Returns: str: The response from the model.
        """
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"""Based on the previous chart analysis below, answer the following question:

                    Previous Analysis:
                    {previous_analysis}

                    Question:
                    {question}"""
                }
            ],
            max_tokens=1500
        )
        

        return response.choices[0].message.content
