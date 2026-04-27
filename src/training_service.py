import time
import os
from src.auto_retrain import optimize_model
from datetime import datetime

def run_continuous_training(duration_hours=1, interval_minutes=5):
    print(f"🚀 [CONTINUOUS LEARNING] Starting 1-hour training marathon...")
    print(f"Interval: every {interval_minutes} minutes | Duration: {duration_hours} hour(s)")
    
    start_time = time.time()
    end_time = start_time + (duration_hours * 3600)
    iteration = 1
    
    os.makedirs("logs", exist_ok=True)
    log_file = "logs/training_marathon.log"
    
    with open(log_file, "a") as f:
        f.write(f"\n--- Training Marathon Started at {datetime.now()} ---\n")

    while time.time() < end_time:
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n🔄 [Iteration {iteration}] Retraining at {current_time}...")
        
        try:
            best_params, best_profit = optimize_model()
            
            log_msg = f"[{current_time}] Iteration {iteration}: Profit ${best_profit:.2f} | Params: {best_params}\n"
            with open(log_file, "a") as f:
                f.write(log_msg)
            
            print(f"✅ Iteration {iteration} complete. Model updated.")
        except Exception as e:
            print(f"❌ Error during training iteration: {e}")
            with open(log_file, "a") as f:
                f.write(f"[{current_time}] Error: {e}\n")
        
        iteration += 1
        # Wait for the next interval
        time.sleep(interval_minutes * 60)
        
    print(f"\n🏆 [MARATHON COMPLETE] Continuous learning service finished at {datetime.now()}.")
    with open(log_file, "a") as f:
        f.write(f"--- Training Marathon Completed at {datetime.now()} ---\n")

if __name__ == "__main__":
    run_continuous_training()
