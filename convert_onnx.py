from optimum.onnxruntime import ORTModelForTokenClassification
from transformers import AutoTokenizer

model_id = "AptaArkana/indonesian_bert_case_model_nergrit"

tokenizer = AutoTokenizer.from_pretrained(model_id)

model = ORTModelForTokenClassification.from_pretrained(
    model_id,
    export=True
)

model.save_pretrained("./onnx_ner")
tokenizer.save_pretrained("./onnx_ner")