# Specify your local folder for storing the model
local_folder = r"C:\Users\prana\Desktop\lambda-chunking\local_models\Qwen2-VL-2B-Instruct"

# Load model directly
from transformers import AutoProcessor, AutoModelForImageTextToText

processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
model = AutoModelForImageTextToText.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")
# Save the model locally
model.save_pretrained(local_folder)
processor.save_pretrained(local_folder)