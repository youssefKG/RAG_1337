QUESTIONS: list[str] = [
    "What activation formats does the fused batched MoE layer return in vLLM?",
    "What are the default values for FP8_MIN and FP8_MAX constants in vLLM's triton_flash_attention module?",
    "What determines whether vLLM's sampler returns Pythonized results or deferred Pythonization arguments?",
    "What's the default value of trust_remote_code in vLLM's LLM class constructor?",
    "What determines the values in cudagraph_inputs_embeds when capturing CUDA graph shapes in vLLM's ModelRunner?",
    "What conditions must be met for vLLM's ModelRunner to use CUDA graphs instead of the regular model?",
    "What is the default timeout value for vLLM RPC operations?",
    "What does the Gemma3ForCausalLM constructor assert about the tie_word_embeddings configuration?",
    "What value is passed for ngroups when has_groups is False in the _bmm_chunk_fwd_kernel call?",
    "What is the default cudagraph_support value for TritonAttentionMetadataBuilder?",
    "What does the get_num_new_matched_tokens method in NIXLConnector return?",
    "What types are supported as containers in vLLM's JSONTree type definition?",
]
