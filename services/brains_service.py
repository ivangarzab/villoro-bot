"""
Brains Service - AI intelligence layer powered by kluvs-brain

Wraps KluvsAgenticEngine + SocraticAgent from kluvs-brain to provide
RAG-powered answers about "Knowledge and Freedom in the Work of Luis Villoro".

Maintains per-user conversation history for contextual Socratic dialogue.
"""
from typing import Dict, List

from kluvs_brain import KluvsAgenticEngine, SocraticAgent, BrainError, RetrievalError, ReasoningError

from utils.constants import BOOK_TITLE, BOOK_SCOPE

MAX_HISTORY = 20  # messages (10 Q&A pairs)


class BrainsService:
    """
    AI service wrapper for kluvs-brain's agentic RAG pipeline.

    Instantiates KluvsAgenticEngine + SocraticAgent once at startup and
    maintains per-user conversation history for contextual Socratic dialogue.

    Attributes:
        agent: SocraticAgent wrapping the KluvsAgenticEngine
        book_title: The full title of the book being queried
        scope: Supabase scope identifier for vector search filtering
    """

    def __init__(self, supabase_url: str, supabase_key: str, openai_key: str):
        """
        Initialize the brains service with API credentials.

        Args:
            supabase_url: Supabase project URL for the brains backend
            supabase_key: Supabase service role key
            openai_key: OpenAI API key for GPT-4o and embeddings

        Raises:
            ValueError: If any required credentials are missing
        """
        if not all([supabase_url, supabase_key, openai_key]):
            raise ValueError("All API credentials required for BrainsService")

        print("[INFO] Initializing BrainsService with KluvsAgenticEngine")
        engine = KluvsAgenticEngine(supabase_url, supabase_key, openai_key)
        self.agent = SocraticAgent(engine)
        self.book_title = BOOK_TITLE
        self.scope = BOOK_SCOPE
        self._history: Dict[int, List[Dict[str, str]]] = {}

        print(f"[INFO] BrainsService initialized — scope: '{self.scope}', book: '{self.book_title}'")

    async def ask(self, user_id: int, question: str) -> str:
        """
        Ask a question about the book using agentic RAG-powered Socratic tutoring.

        Retrieves and updates per-user conversation history so the agent can
        track student progress across turns.

        Args:
            user_id: Discord user ID (int) used to key conversation history
            question: The student's question about the book

        Returns:
            Socratic response with hints, context, and follow-up questions

        Raises:
            RetrievalError: If no knowledge is found or database is unavailable
            ReasoningError: If the AI engine fails to generate a response
            BrainError: For other brain-related errors
        """
        print(f"[INFO] Processing question — scope='{self.scope}', user={user_id}")
        print(f"[INFO] Question: {question}")

        history = self._history.get(user_id, [])

        try:
            response = await self.agent.ask(
                student_query=question,
                scope=self.scope,
                book_title=self.book_title,
                history=history,
            )
            self._update_history(user_id, question, response)
            print(f"[SUCCESS] Response generated for '{self.book_title}'")
            return response

        except RetrievalError as e:
            print(f"[ERROR] RetrievalError: {str(e)}")
            raise

        except ReasoningError as e:
            print(f"[ERROR] ReasoningError: {str(e)}")
            raise

        except BrainError as e:
            print(f"[ERROR] BrainError: {str(e)}")
            raise

        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            raise BrainError(f"Unexpected error: {str(e)}")

    def _update_history(self, user_id: int, question: str, response: str):
        history = self._history.setdefault(user_id, [])
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})
        if len(history) > MAX_HISTORY:
            self._history[user_id] = history[-MAX_HISTORY:]
