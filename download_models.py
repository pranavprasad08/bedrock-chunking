# Specify your local folder for storing the model
local_folder = r"C:\Users\prana\Desktop\lambda-chunking\local_models\Florence-2-base-ft"

from transformers import AutoProcessor, AutoModelForCausalLM 
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForCausalLM.from_pretrained("microsoft/Florence-2-base-ft", torch_dtype=torch_dtype, trust_remote_code=True).to(device)
processor = AutoProcessor.from_pretrained("microsoft/Florence-2-base-ft", trust_remote_code=True)

model.save_pretrained(local_folder)
processor.save_pretrained(local_folder)