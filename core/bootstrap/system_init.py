"""
System initialization for Aletheia Kernel v1.0.
Loaded on startup: config, memory, LLM check, agent warmup.
"""

from memory.service import retrieve_context_nodes  # test init
from memory.storage import init_db  # assume exists or stub
from ai.ollama_client import healthcheck  # will add
from core.contracts.contract_lock import freeze_contract_version
from config.modes import get_mode

def init_system(mode: str = "DEV"):
    """
    Initialize complete Aletheia system.
    """
    print("🧠 Initializing Aletheia Kernel v1.0...")
    
    mode_config = get_mode(mode)
    
    # 1. Memory engine
    try:
        init_db()  # Initialize SQLite/ storage
        # Test retrieval
        nodes = retrieve_context_nodes("test")
        print(f"✅ Memory ready. Loaded {len(nodes)} test nodes.")
    except Exception as e:
        print(f"⚠️  Memory warning: {e}")

    # 1b. Cognitive traces table (idempotent migration)
    try:
        from core.tracing.store import init_traces_table
        init_traces_table()
        print("✅ Cognitive traces table ready.")
    except Exception as e:
        print(f"⚠️  Traces table warning: {e}")

    # 1c. Strategy degradation table
    try:
        from core.cognition.degradation import strategy_degradation
        strategy_degradation._init()
        print("✅ Strategy degradation table ready.")
    except Exception as e:
        print(f"⚠️  Degradation table warning: {e}")

    # 1d. Cognitive replay table
    try:
        from core.tracing.replay import replay_store
        replay_store._init()
        print("✅ Cognitive replay table ready.")
    except Exception as e:
        print(f"⚠️  Replay table warning: {e}")

    # 1e. Cognitive patterns table
    try:
        from core.cognition.pattern_detector import pattern_detector
        pattern_detector._init()
        print("✅ Cognitive patterns table ready.")
    except Exception as e:
        print(f"⚠️  Patterns table warning: {e}")
    
    # 2. LLM / Ollama
    try:
        llm_status = healthcheck()
        print(f"✅ LLM: {llm_status}")
    except Exception as e:
        print(f"❌ LLM error: {e}")
    
    # 3. Contract lock
    contract_v = freeze_contract_version()
    print(f"✅ Contract: v{contract_v}")
    
    # 4. Config / modes
    print(f"✅ Mode: {mode} ({mode_config['verbose']})")
    
    print("🚀 Aletheia Kernel ready!")

