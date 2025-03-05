# tracking/ai_scaling.py
import sys
import os
import subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Replace direct SQLite with database manager
from core.database_manager import get_log_db_manager
from core.error_framework import safe_execute
from core.utility_functions import load_json_state, save_json_state

# Get database manager once
db_manager = get_log_db_manager()

INSTANCE_COUNT = 1  # Base instance count, dynamically modified

class AIScalingManager:
    """Manages AI execution scaling based on processing needs and workload distribution."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "active_instances": INSTANCE_COUNT, 
            "scaling_events": []
        }
        # No need to initialize database here anymore

    @safe_execute
    def monitor_workload(self):
        """Analyzes workload and determines if scaling is needed."""
        try:
            # Simulated system load detection
            cpu_usage = subprocess.check_output(["grep", "cpu", "/proc/stat"]).decode("utf-8")
            if "cpu" in cpu_usage:
                load_factor = cpu_usage.count(" ") / 100  # Simulated CPU-based load factor

                # Use the database manager for queries
                scale_up_count = db_manager.execute(
                    "SELECT COUNT(*) as count FROM ai_scaling WHERE event_type='scale_up'"
                )[0]['count']
                
                scale_down_count = db_manager.execute(
                    "SELECT COUNT(*) as count FROM ai_scaling WHERE event_type='scale_down'"
                )[0]['count']

                active_instances = scale_up_count - scale_down_count + 1  # Base instance count is 1

                if load_factor > 0.75:
                    print("⚠️ High AI workload detected. Scaling up execution instances.")
                    self.scale_up(active_instances)
                elif load_factor < 0.25 and active_instances > 1:
                    print("✅ Low AI workload detected. Scaling down unnecessary instances.")
                    self.scale_down(active_instances)

                return {"success": True, "active_instances": active_instances}
        except Exception as e:
            print(f"⚠️ Workload monitoring failed: {str(e)}")
            return {"success": False, "error": str(e)}

    @safe_execute
    def scale_up(self, active_instances):
        """Increases the number of AI execution instances if demand requires it."""
        active_instances += 1
        instance_id = f"instance_{active_instances}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Launch a new AI instance
        subprocess.Popen(["python3", "core/multi_agent.py"])

        # Use database manager instead of direct connection
        db_manager.execute_update(
            "INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
            ("scale_up", instance_id, active_instances)
        )

        print(f"🚀 AI execution scaled up. New instance: {instance_id}")
        return {"success": True, "instance_id": instance_id}
        
    @safe_execute
    def scale_down(self, active_instances):
        """Reduces AI execution instances when workload is low."""
        if active_instances > 1:
            active_instances -= 1
            instance_id = f"instance_{active_instances}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            db_manager.execute_update(
                "INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
                ("scale_down", instance_id, active_instances)
            )

            print(f"📉 AI execution scaled down. Instance {instance_id} removed.")
            return {"success": True, "instance_id": instance_id}
        return {"success": False, "message": "Cannot scale down, already at minimum instances"}

    @safe_execute
    def synchronize_instances(self):
        """Ensures AI instances communicate and share updates."""
        print("🔄 Synchronizing AI instances across execution environments...")

        db_manager.execute_update(
            "INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
            ("synchronization", "sync_event", 0)
        )
        return {"success": True, "message": "Instances synchronized"}

    @safe_execute
    def review_scaling_status(self):
        """Displays current AI scaling status."""
        logs = db_manager.execute(
            "SELECT timestamp, event_type, instance_id, active_instances FROM ai_scaling ORDER BY timestamp DESC"
        )

        print("\n📊 AI Scaling Report:")
        for log in logs:
            print(f"🔹 {log['timestamp']} | {log['event_type'].upper()} | " +
                  f"Instance: `{log['instance_id']}` | Active Instances: {log['active_instances']}")
        
        return {"success": True, "logs": logs}

if __name__ == "__main__":
    scaling_manager = AIScalingManager()
    scaling_manager.monitor_workload()
    scaling_manager.synchronize_instances()
    scaling_manager.review_scaling_status()
