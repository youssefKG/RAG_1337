from . import config_manager

# print(config_manager.update(is_indexing_hybrid=True, search_type="lexical", max_chunk_size=2000))
config_manager.write_default_config()
