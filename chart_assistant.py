import os
import time
import base64
import io
from unittest import result
from config import Config
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

class ChartsAssistant: 
    def __init__(self):
        Config.validate_env_variables()
        self.openai_client = Config.get_openai_client()
        self.vision_client = Config.get_vision_client()
    
    async def analyze_chart(self, files):
        """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data."""
        image_bytes_dict = {}
        base64_images_dict = {}
        all_text_results = []
        
        for filename, image_data in files:
            if isinstance(image_data, bytes):
                image_bytes_dict[filename] = image_data
                base64_images_dict[filename] = base64.b64encode(image_data).decode('utf-8')
            else:
                # Already base64
                image_bytes_dict[filename] = base64.b64decode(image_data)
                base64_images_dict[filename] = image_data
                

        # Read operation for OCR from file
        print("Extracting text with OCR...")
        counter = 0
        for filename, image_bytes in image_bytes_dict.items():
            if counter < 5:
                image_stream = io.BytesIO(image_bytes)
                image_stream.seek(0) 
                read_result = self.vision_client.read_in_stream(
                    image_stream,
                    raw=True
                )
            
                # Extract operation ID
                operation_id = read_result.headers["Operation-Location"].split("/")[-1]
                
                print(f"Operation ID: {operation_id}")
                # wait for the operation to complete
                result = self._poll_for_result(operation_id)
            
                # Extracting text 
                print(f"result: {result}")
                analyze_result = result.get('analyze_result') if isinstance(result, dict) else result.analyze_result
                
                # Create a separate list for this file's text items
                file_text_items = []
                if analyze_result and hasattr(analyze_result, 'read_results'):
                    for page in analyze_result.read_results:
                        for line in page.lines:
                            file_text_items.append({
                                'text': line.text,
                                'bbox': line.bounding_box
                            })
                
                # Extract text from THIS file only
                extracted_text = "\n".join([item['text'] for item in file_text_items])
                
                print(f"Extracted Text for {filename}:\n{extracted_text}\n")
                
                # Now append to all_text_results as a tuple
                all_text_results.append((filename, extracted_text))
                counter += 1
            
        print("Analyzing with GPT-4 Vision...")
        
        ocr_summary = "\n\n".join([f"**{filename}:**\n{text}" for filename, text in all_text_results])

        content = [
                        {
                            "type": "text",
                            "text": f"""Analyze this chart and create a structured interpretation.

                            OCR extracted this text (but positions may be jumbled):
                            {ocr_summary}

                            For each file please:
                            1. Identify if there is any chart included and if so, write its title.
                            2. Identify the chart type (pie chart, bar chart, etc.)
                            3. Connect each company/label to its correct percentage by looking at the visual layout
                            4. If it's possible, describe the market share distribution
                            5. Identify trends 
                            6. Provide insights about the data
                            
                            And finally, create a concise summary to explain visualize report like: "The chart shows a 15% increase of sales in Q2". 
                            If it's possible provide correlation and dependencies between charts.

                            Create a clear table showing: Company Name | Market Share %"""
                        }
                    ]
        
        for filename in all_text_results:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_images_dict[filename[0]]}"
                }
            })
            
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
                    "content": content      
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
                    "content": """You are an expert at analyzing charts and graphs. 
                    You can see the visual layout and understand which data points connect to which labels.
                    Provide structured analysis with correct data associations."""
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