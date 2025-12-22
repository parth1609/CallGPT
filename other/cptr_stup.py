import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from backend import _pipeline as pipeline
from backend.conversation import thread_manager

# Setup checkpointer
db_path = os.path.join("db", "chatbot.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)
conn = sqlite3.connect(database=db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# Build the graph
chatbot = pipeline.build_rag_graph(checkpointer=checkpointer)

# Get all threads
all_threads = set()
for checkpoint in checkpointer.list(None):
    all_threads.add(checkpoint.config["configurable"]["thread_id"])

print("All thread IDs:", list(all_threads))
print(checkpointer.setup())

# Load and print conversations for each thread
for thread_id in all_threads:
    print(f"\n--- Conversation for thread {thread_id} ---")
    messages = thread_manager.load_conversation(chatbot, thread_id)
    for msg in enumerate(messages):
        print(msg)


"""

{
  "threads": [
    {
      "thread_id": "1828b29e-ca3a-41a1-a5ed-4fb58e07b168",
      "conversation": [
        {
          "index": 0,
          "type": "HumanMessage",
          "content": "my name is yash",
          "id": "ae2c0e2e-10b1-4bc7-853c-1cc18a455f7b"
        },
        {
          "index": 1,
          "type": "HumanMessage",
          "content": "my name is yash",
          "id": "c84e84d8-8bff-47de-af7d-77012aaba89f"
        },
        {
          "index": 2,
          "type": "AIMessage",
          "content": "Hello Yash, nice to meet you! How can I help you today?",
          "id": "3907ed85-c7f8-4375-94a4-5dc7a54af8d3"
        },
        {
          "index": 3,
          "type": "HumanMessage",
          "content": "what is iran trap? acknowledge with my name.",
          "id": "2c046eb9-e4a9-478f-9d81-ebf1192dd510"
        },
        {
          "index": 4,
          "type": "HumanMessage",
          "content": "what is iran trap? acknowledge with my name.",
          "id": "9759f030-c8cc-49ab-9137-bfc27beb4dea"
        },
        {
          "index": 5,
          "type": "AIMessage",
          "content": "Sure thing, Yash. I’m sorry, but I don’t have information on something called an “Iran trap” in the material I have. Is there anything else I can help you with?",
          "id": "cecd4a9e-6b11-4b2d-8ad7-330f600a7b84"
        },
        {
          "index": 6,
          "type": "HumanMessage",
          "content": "what is iran against USA? acknowledge with my name.",
          "id": "ca650df5-7538-4af4-84cf-266929a9a413"
        },
        {
          "index": 7,
          "type": "HumanMessage",
          "content": "what is iran against USA? acknowledge with my name.",
          "id": "8b3c4f55-ede2-4515-b01c-fcb3c111877b"
        },
        {
          "index": 8,
          "type": "AIMessage",
          "content": "Sure thing, Yash. Based on the information we have, Iran is portrayed as a key adversary to the United States in the current geopolitical landscape. The material suggests that the U.S. sees Iran as a potential challenge to its military dominance—so much so that some argue America might even consider a direct military action, like an invasion, to reaffirm its hegemony. The tension is highlighted by events such as the 2020 assassination of Iran’s senior commander Qasem\u202fSoleimani, which underscored how hostile the relationship has become. In short, Iran is depicted as a major rival to U.S. interests in the Middle East.",
          "id": "86e52c83-0faa-4b95-a67c-2c87ae911c99"
        },
        {
          "index": 9,
          "type": "HumanMessage",
          "content": "explain about middle east tesions.",
          "id": "2a8fc83d-b994-4c9d-9593-f00ea62f544b"
        },
        {
          "index": 10,
          "type": "HumanMessage",
          "content": "explain about middle east tesions.",
          "id": "a5e55132-755d-4754-b123-635904eaa93b"
        },
        {
          "index": 11,
          "type": "AIMessage",
          "content": "Sure thing, Yash.  \n\nThe tensions in the Middle East stem from a mix of historic rivalries, regional power struggles, and outside influences.\u202fHere’s a quick rundown based on what we have:\n\n1. **Saudi‑Iran rivalry** – Saudi Arabia and Iran see each other as the main challengers for regional dominance. Saudi leaders view Iran’s influence as a direct threat, and vice‑versa, which fuels proxy wars and diplomatic friction.\n\n2. **1979 turning points**  \n   * **Iran’s Islamic Revolution** toppled the pro‑U.S. monarchy and installed an Islamic Republic that demanded no U.S. interference and a government based on Islamic law.  \n   * **The Mecca siege** later that year saw Saudi extremists demand the same—U.S. withdrawal and rule by Islamic law—highlighting how both countries faced internal pressure to adopt stricter religious governance.\n\n3. **Proxy conflicts** – The Houthis in Yemen, backed by Iran, have used cheap drones to strike Saudi oil facilities and desalination plants, causing massive economic damage and civilian casualties. That conflict has drawn in a U.S.–led coalition of about 30 nations, using “shock and awe” tactics that further inflame regional animosities.\n\n4. **U.S. involvement** – American strategic goals, such as maintaining empire‑level influence and supporting allies like Israel, add another layer. Some argue that U.S. actions—like the 2020 killing of Iran’s commander Qasem\u202fSoleimani—are meant to keep any regional power from challenging American supremacy.\n\nAll of these factors—historical revolutions, religious‑driven demands, proxy wars, and great‑power politics—interlock to keep the Middle East in a state of ongoing tension.  \n\nAnything else you’d like to dive into?",
          "id": "1d17d5f0-21e4-4b4c-aa1f-affe2dd265fa"
        }
      ]
    },
    {
      "thread_id": "41300162-73fa-4365-aa94-de6a4a927e01",
      "conversation": [
        {
          "index": 0,
          "type": "HumanMessage",
          "content": "this is parh",
          "id": "3e4bb05d-1c5c-4f77-b673-68d5e675dbc3"
        },
        {
          "index": 1,
          "type": "HumanMessage",
          "content": "this is parh",
          "id": "c172b1da-229e-4708-b86f-194491f15168"
        },
        {
          "index": 2,
          "type": "AIMessage",
          "content": "I’m sorry, but I don’t have any information on that. Could you please provide a bit more detail or clarify your question?",
          "id": "380c33f6-86d9-4d71-bc48-9afbc74e6ce9"
        },
        {
          "index": 3,
          "type": "HumanMessage",
          "content": "tell me about USA",
          "id": "3969687a-0d7c-4b2b-9853-ce82376fab5d"
        },
        {
          "index": 4,
          "type": "HumanMessage",
          "content": "tell me about USA",
          "id": "8072c70a-5f2c-4ea5-a301-bad962d527f5"
        },
        {
          "index": 5,
          "type": "AIMessage",
          "content": "Sure, here’s a quick overview based on what we have:\n\nThe United\u202fStates is portrayed as having overwhelming military advantages. It controls the skies with what’s described as the world’s greatest air force, and it operates an extensive satellite network that can monitor virtually everything and intercept electronic communications. Its special‑forces units are highlighted as elite troops who can operate deep behind enemy lines and direct air power.\n\nThe 2003 Gulf War is used as an example of that power in action. The “shock and awe” strategy—though once called unrealistic—was said to have worked exactly as planned, resulting in a three‑week conflict where roughly 130,000 U.S. troops defeated 370,000 Iraqi soldiers, with U.S. casualties kept under 200.\n\nHowever, the text also points out a key limitation: the U.S. lacks a large manufacturing base, meaning it can’t sustain a prolonged, large‑scale war as easily as some rivals. The overall argument is that America maintains its global dominance by projecting overwhelming force, especially through air power and special‑operations missions, while relying on the perception of empire to keep other nations in check.",
          "id": "e738793e-2fdf-4250-8fb8-5a9e17ae06d7"
        }
      ]
    }
  ]
}
"""
