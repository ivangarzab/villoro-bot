"""
Brains Service - AI intelligence layer powered by kluvs-brain

Wraps KluvsAgenticEngine + SocraticAgent from kluvs-brain to provide
RAG-powered answers about "Knowledge and Freedom in the Work of Luis Villoro".

Maintains per-channel conversation history for contextual Socratic dialogue.
History is scoped to the channel so all students in a server channel share
the same conversation thread (public Socratic discussion), while DM channels
and threads remain naturally isolated.
"""
import uuid
from typing import Dict, List, NamedTuple

from kluvs_brain import KluvsAgenticEngine, SocraticAgent, BrainError, RetrievalError, ReasoningError

from utils.constants import BOOK_TITLE, BOOK_SCOPE

MAX_HISTORY = 20  # messages (10 Q&A pairs)


class AskResult(NamedTuple):
    response: str
    conversation_id: str


class BrainsService:
    """
    AI service wrapper for kluvs-brain's agentic RAG pipeline.

    Instantiates KluvsAgenticEngine + SocraticAgent once at startup and
    maintains per-channel conversation history for contextual Socratic dialogue.

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
        self._conversation_ids: Dict[int, str] = {}

        print(f"[INFO] BrainsService initialized — scope: '{self.scope}', book: '{self.book_title}'")

    def _get_session(self, channel_id: int):
        """Return (history, conversation_id) for a channel, creating one if needed."""
        if channel_id not in self._conversation_ids:
            self._history[channel_id] = []
            self._conversation_ids[channel_id] = str(uuid.uuid4())
        return self._history[channel_id], self._conversation_ids[channel_id]

    async def ask(self, user_id: int, channel_id: int, question: str) -> AskResult:
        """
        Ask a question about the book using agentic RAG-powered Socratic tutoring.

        Retrieves and updates per-channel conversation history so the agent can
        track the discussion across turns. All students in the same channel share
        the same history; DMs and threads are naturally isolated by their channel ID.

        Args:
            user_id: Discord user ID (used for logging only)
            channel_id: Discord channel ID used to scope conversation history
            question: The student's question about the book

        Returns:
            AskResult with the Socratic response and the active conversation_id

        Raises:
            RetrievalError: If no knowledge is found or database is unavailable
            ReasoningError: If the AI engine fails to generate a response
            BrainError: For other brain-related errors
        """
        print(f"[INFO] Processing question — scope='{self.scope}', user={user_id}, channel={channel_id}")
        print(f"[INFO] Question: {question}")

        history, conversation_id = self._get_session(channel_id)

        try:
            response = await self.agent.ask(
                student_query=question,
                scope=self.scope,
                book_title=self.book_title,
                history=history,
            )
            self._update_history(channel_id, question, response)
            print(f"[SUCCESS] Response generated for '{self.book_title}'")
            return AskResult(response=response, conversation_id=conversation_id)

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

    def _update_history(self, channel_id: int, question: str, response: str):
        history = self._history.setdefault(channel_id, [])
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response})
        if len(history) > MAX_HISTORY:
            self._history[channel_id] = history[-MAX_HISTORY:]
