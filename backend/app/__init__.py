import os

# XGBoost/sklearn and torch each bring their own OpenMP runtime. With both loaded
# and more than one OpenMP thread, DistilBERT inference deadlocks (every /chat
# request hangs). One thread per op avoids it; inputs here are tiny, so the cost
# is negligible. Must run before any ML library is imported. Phase 3 revisits this.
os.environ.setdefault("OMP_NUM_THREADS", "1")
