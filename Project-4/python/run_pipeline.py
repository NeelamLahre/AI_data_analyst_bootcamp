# python/run_pipeline.py
import logging, subprocess, sys

logging.basicConfig(
    filename="logs/pipeline.log", level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s")

STEPS = ["01_profile.py", "02_clean.py", "03_load.py", "03b_load_claims.py",
         "03c_backfill_rider_fields.py", "03d_backfill_sentiment.py",
         "03e_backfill_agent_fields.py"]

for step in STEPS:
    logging.info("START %s", step)
    outcome = subprocess.run([sys.executable, f"python/{step}"],
                              capture_output=True, text=True)
    if outcome.returncode != 0:
        logging.error("FAILED %s\n%s", step, outcome.stderr)
        raise SystemExit(f"Pipeline stopped at {step}")
    logging.info("DONE %s", step)

print("Pipeline completed successfully")