import logging
from monitor.services import MonitorService
from monitor.models import Monitor

# 1. Setup Logger to ensure we see the output in the console
logger = logging.getLogger("app.monitor.services")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('👉 %(message)s'))
logger.addHandler(handler)

# 2. Get a Monitor
monitor = Monitor.objects.first()
if not monitor:
    print("❌ No monitors found! Create one in the dashboard first.")
else:
    # Force it UP so anomaly detection runs (it only runs on UP monitors)
    monitor.status = "UP"
    monitor.save()
    
    print(f"🧪 Testing Anomaly Detection on: '{monitor.name}'")

    service = MonitorService()

    # 3. Establish Baseline (Training Phase)
    # We generate 20 checks with ~100ms latency
    print("... 📉 Generating 20 'normal' heartbeats (100-105ms) ...")
    for i in range(20):
        service.process_check_result(
            monitor_id=monitor.id,
            is_up=True,
            response_time=100 + (i % 5), # Small jitter (100, 101, 102...)
            status_code=200
        )

    # 4. Trigger Anomaly (Testing Phase)
    # We inject a 500ms spike.
    # Avg ~102ms, Stdev ~2.  Value 500 is ~200 Standard Deviations away!
    print("... 💥 INJECTING ANOMALY (500ms) ...")
    
    service.process_check_result(
        monitor_id=monitor.id,
        is_up=True,
        response_time=500, 
        status_code=200
    )

    print("✅ Test Complete.")
