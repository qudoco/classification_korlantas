from transformers import pipeline
from optimum.onnxruntime import ORTModelForTokenClassification
from transformers import AutoTokenizer
import warnings
warnings.filterwarnings("ignore", message=".*mistral.*")

MODEL_PATH = "./onnx_ner"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    use_fast=True
)

model = ORTModelForTokenClassification.from_pretrained(
    MODEL_PATH
)

ner_pipe = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple"
)