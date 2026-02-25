"""
Brains Service - AI intelligence layer powered by kluvs-brain

Wraps the SocraticEngine from kluvs-brain to provide RAG-powered
answers about "Knowledge and Freedom in the Work of Luis Villoro".
"""
from kluvs_brain import SocraticEngine, BrainError, RetrievalError, ReasoningError

from utils.constants import BOOK_TITLE, BOOK_SCOPE


class BrainsService:
    """
    AI service wrapper for kluvs-brain's SocraticEngine.

    Provides a Discord-bot-friendly async interface to the RAG backend,
    using Socratic tutoring methodology to guide students through the book.

    Attributes:
        engine: The underlying SocraticEngine from kluvs-brain
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

        print("[INFO] Initializing BrainsService with SocraticEngine")
        self.engine = SocraticEngine(supabase_url, supabase_key, openai_key)
        self.book_title = BOOK_TITLE
        self.scope = BOOK_SCOPE

        print(f"[INFO] BrainsService initialized — scope: '{self.scope}', book: '{self.book_title}'")

    async def ask(self, question: str) -> str:
        """
        Ask a question about the book using RAG-powered Socratic tutoring.

        Args:
            question: The student's question about the book

        Returns:
            Socratic response with hints, context, and follow-up questions

        Raises:
            RetrievalError: If no knowledge is found or database is unavailable
            ReasoningError: If the AI engine fails to generate a response
            BrainError: For other brain-related errors
        """
        print(f"[INFO] Processing question — scope='{self.scope}'")
        print(f"[INFO] Question: {question}")

        try:
            response = await self.engine.ask(
                student_query=question,
                scope=self.scope,
                book_title=self.book_title
            )
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
