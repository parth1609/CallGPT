import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())


def check_import(module_name):
    try:
        __import__(module_name)
        print(f"✅ Import successful: {module_name}")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {module_name} - {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing {module_name}: {e}")
        return False


def verify_services():
    print("\n--- Verifying Service Initialization ---")
    load_dotenv()

    services = [
        ("app.modules.embedding.service", "EmbeddingService"),
        ("app.modules.retrieval.service", "RetrievalService"),
        ("app.modules.llm.service", "LLMService"),
        ("app.modules.conversation.service", "ConversationService"),
        ("app.modules.document.service", "DocumentService"),
        ("app.modules.vectorstore.service", "VectorStoreService"),
    ]

    for module_path, class_name in services:
        try:
            module = __import__(module_path, fromlist=[class_name])
            service_class = getattr(module, class_name)
            # Try to initialize (might fail if env vars are missing, which is what we want to catch)
            try:
                service = service_class()
                print(f"✅ Initialized: {class_name}")
            except Exception as e:
                print(f"❌ Failed to initialize {class_name}: {e}")
        except Exception as e:
            print(f"❌ Failed to load module for {class_name}: {e}")


if __name__ == "__main__":
    print("--- Checking Imports ---")
    modules_to_check = [
        "app.main",
        "app.modules.pipeline.router",
        "app.modules.embedding.router",
        "app.modules.retrieval.router",
        "app.modules.llm.router",
        "app.modules.conversation.router",
        "app.modules.document.router",
        "app.modules.vectorstore.router",
    ]

    all_passed = True
    for mod in modules_to_check:
        if not check_import(mod):
            all_passed = False

    if all_passed:
        verify_services()
    else:
        print("\n❌ Fix import errors before checking services.")
