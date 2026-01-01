# import os
# import yaml
# from pathlib import Path
# from dotenv import load_dotenv

# load_dotenv()

# class Config:
#     """Configuration manager for evaluation system"""
    
#     def __init__(self, config_path='config.yaml'):
#         self.root_dir = Path(__file__).parent.parent
#         self.config_path = self.root_dir / config_path
        
#         # Load YAML config
#         with open(self.config_path, 'r') as f:
#             self.config = yaml.safe_load(f)
        
#         # API Keys
#         self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
#         self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
#         # Paths
#         self.data_dir = self.root_dir / 'data'
#         self.test_cases_dir = self.data_dir / 'test_cases'
#         self.ground_truth_dir = self.data_dir / 'ground_truth'
#         self.results_dir = self.data_dir / 'results'
        
#         # Create directories if they don't exist
#         for dir_path in [self.test_cases_dir, self.ground_truth_dir, self.results_dir]:
#             dir_path.mkdir(parents=True, exist_ok=True)
    
#     def get_weights(self, mode='cold_start'):
#         """Get evaluation weights for specified mode"""
#         return self.config['weights'].get(mode, self.config['weights']['cold_start'])
    
#     def get_thresholds(self):
#         """Get quality thresholds"""
#         return self.config['thresholds']
    
#     def get_llm_config(self):
#         """Get LLM judge configuration"""
#         return self.config['llm_judge']
    
#     def get_safety_config(self):
#         """Get safety evaluation configuration"""
#         return self.config['safety']

# config = Config()