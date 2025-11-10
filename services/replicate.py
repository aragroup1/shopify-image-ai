import replicate
import os
from dotenv import load_dotenv
from utils import track_cost

load_dotenv()

class ReplicateService:
    def __init__(self):
        self.client = replicate.Client(api_token=os.getenv('REPLICATE_API_TOKEN'))
        self.daily_cost = 0.0
        self.budget = float(os.getenv('DAILY_BUDGET', 5.00))
    
    def run_model(self, model_name, input_data, cost_per_run=0.001):
        """Run model with budget protection"""
        if self.daily_cost + cost_per_run > self.budget:
            raise Exception(f"Daily budget exceeded (${self.budget})")
        
        output = self.client.run(model_name, input=input_data)
        self.daily_cost += cost_per_run
        track_cost(cost_per_run)  # Persist cost tracking
        return output
