import argparse
import asyncio
import sys
from uuid import UUID
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, dispose_engine
from app.models.rag import AIConversation, AIMessage


async def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect safe conversation memory metadata")
    parser.add_argument("conversation_id", type=UUID); args = parser.parse_args()
    try:
        async with AsyncSessionLocal() as session:
            conversation = await session.get(AIConversation, args.conversation_id)
            if conversation is None: raise ValueError("conversation not found")
            messages = list((await session.scalars(select(AIMessage).where(
                AIMessage.conversation_id == conversation.id).order_by(AIMessage.sequence_number))).all())
            print(f"conversation_id={conversation.id} messages={len(messages)} summary_until={conversation.summary_until_sequence} has_summary={str(bool(conversation.summary)).lower()}")
            for message in messages:
                print(f"sequence={message.sequence_number} role={message.role.value} rewritten={message.rewritten_question or '-'} refused={str(bool((message.metadata_ or {}).get('refused'))).lower()}")
    finally: await dispose_engine()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
