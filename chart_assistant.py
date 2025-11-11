import os
import time
import base64
import io
from config import Config
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

class ChartsAssistant: 
    def __init__(self):
        Config.validate_env_variables()
        self.openai_client = Config.get_openai_client()
        self.vision_client = Config.get_vision_client()
    
    def analyze_chart(self, image_data):
        """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data."""
        if isinstance(image_data, bytes):
            base64_image = base64.b64encode(image_data).decode('utf-8')
        else:
            base64_image = image_data

        # Read operation for OCR from file
        print("Extracting text with OCR...")
        read_result = self.vision_client.read_in_stream(
            io.BytesIO(image_data),
            raw=True
        )
        
        # Extract operation ID
        operation_id = read_result.headers["Operation-Location"].split("/")[-1]
        
        # wait for the operation to complete
        result = self._poll_for_result(operation_id)
        
        # Extracting text 
        # TODO: improve extracting text positions to better associate labels with data points
        text_results = []
        if result:
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    text_results.append({
                    'text': line.text,
                    'bbox': line.bounding_box  # Position information
                })
            
        extracted_text = "\n".join([item['text'] for item in text_results])
        print("Analyzing with GPT-4 Vision...")
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at analyzing charts and graphs. 
                    You can see the visual layout and understand which data points connect to which labels.
                    Provide structured analysis with correct data associations."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this chart and create a structured interpretation.

                            OCR extracted this text (but positions may be jumbled):
                            {extracted_text}

                            Please:
                            1. Identify the chart type (pie chart, bar chart, etc.)
                            2. Connect each company/label to its correct percentage by looking at the visual layout
                            3. Describe the market share distribution
                            4. Identify trends (who has the largest/smallest share)
                            5. Provide insights about the data

                            Create a clear table showing: Company Name | Market Share %"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    
    def _poll_for_result(self, operation_id, max_attempts=30, poll_interval=1):
        """Poll for Read operation result"""
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
                time.sleep(poll_interval)
            except Exception as e:
                print(f" ✗ Error polling: {str(e)}")
                return None
        
        print(" ✗ Timeout")
        return None

    def followup_response(self, question, previous_analysis):
        """Generate follow-up response based on previous analysis."""
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert assistant that helps users understand chart analyses."
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
            max_tokens=1000
        )
        
        return response.choices[0].message.content