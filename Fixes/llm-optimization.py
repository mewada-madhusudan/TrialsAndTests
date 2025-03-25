import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

class OptimizedLLMProcessor:
    def __init__(
        self, 
        model_name: str = "microsoft/Orca-2-7b", 
        use_cpu: bool = False,
        max_context_length: int = 1024
    ):
        """More efficient LLM initialization"""
        try:
            # Use more efficient quantization
            quantization_config = BitsAndBytesConfig(
                load_in_8bit=True,
                llm_int8_threshold=6.0
            ) if not use_cpu else None
            
            # Load with more efficient settings
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto" if not use_cpu else "cpu",
                torch_dtype=torch.float16 if not use_cpu else torch.float32,
                quantization_config=quantization_config,
                low_cpu_mem_usage=True
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # More efficient pipeline
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=max_context_length,
                do_sample=False,
                return_full_text=False
            )
        except Exception as e:
            logger.error(f"Optimized LLM initialization error: {e}")
            raise

    def batch_process(self, prompts: List[str], batch_size: int = 4) -> List[str]:
        """Process prompts in batches for efficiency"""
        results = []
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            batch_results = self.pipe(batch)
            results.extend([res[0]['generated_text'] for res in batch_results])
        return results
