import os

# Dummy keys so modules that build clients at import time can load in tests.
os.environ.setdefault("OPENAI_API_KEY", "test-key")
