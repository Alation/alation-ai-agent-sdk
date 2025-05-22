"""
Data Catalog QA Chatbot - An intelligent question-answering system using the Alation SDK.

This example demonstrates:
1. Using Alation's internal LLM-powered context retrieval
2. Building effective signatures with required and optional fields
3. Creating a conversational interface with context memory
4. Passing raw Alation context directly to the LLM

IMPORTANT: This is an example implementation. In a production environment,
you would want to enhance how follow-up questions are handled. Currently,
the implementation calls Alation's context API for every question, which may
return incorrect or irrelevant results for follow-up questions that reference
previous conversation

Usage:
    python data_catalog_qa.py [--question "your question"] [--conversation]

Environment variables:
    ALATION_BASE_URL: URL of your Alation instance
    ALATION_USER_ID: Your Alation user ID
    ALATION_REFRESH_TOKEN: Your Alation refresh token
    OPENAI_API_KEY: Your OpenAI API key
"""

import os
import json
import argparse
from typing import Dict, Any, List

import openai
from alation_ai_agent_sdk import AlationAIAgentSDK, UserAccountAuthParams, ServiceAccountAuthParams
from alation_ai_agent_sdk.api import AlationAPIError


class DataCatalogQA:
    """Question answering system for data catalog exploration."""

    def __init__(self):
        """Initialize the QA system with Alation SDK and OpenAI client."""

        # Load credentials
        self.base_url = os.getenv("ALATION_BASE_URL")
        user_id_str = os.getenv("ALATION_USER_ID")
        self.refresh_token = os.getenv("ALATION_REFRESH_TOKEN")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # Validate environment variables
        if not all([self.base_url, user_id_str, self.refresh_token]):
            raise ValueError(
                "Missing Alation credentials. Please set ALATION_BASE_URL, "
                "ALATION_USER_ID, and ALATION_REFRESH_TOKEN environment variables."
            )

        if not openai_api_key:
            raise ValueError(
                "Missing OpenAI API key. Please set OPENAI_API_KEY environment variable."
            )

        # Convert user_id to int
        try:
            self.user_id = int(user_id_str)
        except ValueError:
            raise ValueError(f"ALATION_USER_ID must be an integer, got: {user_id_str}")

        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=openai_api_key)

        # Load auth method from env
        auth_method = os.getenv("ALATION_AUTH_METHOD", "user_account")

        # Initialize Alation SDK
        self.sdk = AlationAIAgentSDK(
            base_url=self.base_url,
            auth_method=auth_method,  # Use auth_method from env
            auth_params=UserAccountAuthParams(
                user_id=self.user_id, refresh_token=self.refresh_token
            ) if auth_method == "user_account" else ServiceAccountAuthParams(
                client_id=os.getenv("ALATION_CLIENT_ID"),
                client_secret=os.getenv("ALATION_CLIENT_SECRET")
            )
        )

        # Initialize conversation history (including context)
        self.conversation_history = []

    def create_comprehensive_signature(self) -> Dict[str, Any]:
        """
        Create a comprehensive signature that leverages Alation's dynamic field selection.

        Uses fields_required for essential info and fields_optional for content
        that should be included only when relevant to the question.
        """
        return {
            "table": {
                "fields_required": ["name", "title", "description", "url"],
                "fields_optional": ["common_joins", "common_filters", "columns"],
                "child_objects": {
                    "columns": {"fields": ["name", "data_type", "description", "sample_values"]}
                },
            },
            "documentation": {
                "fields_required": ["title", "url", "content"],
            },
            "query": {"fields_required": ["title", "description", "content", "url"]},
        }

    def get_catalog_context(self, question: str) -> Dict[str, Any]:
        """
        Retrieve relevant context from the Alation catalog.

        Leverages Alation's internal LLM for query understanding and dynamic field selection.
        """
        # Create a comprehensive signature with required and optional fields
        signature = self.create_comprehensive_signature()

        try:
            # Get context from Alation - the internal LLM will handle query rewriting
            # and intelligently select from optional fields based on the question
            return self.sdk.get_context(question, signature)
        except AlationAPIError as e:
            print(f"Error retrieving context: {e}")
            return {}

    def combine_contexts(self, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine multiple context objects into a single unified context.

        Args:
            contexts: List of context dictionaries from Alation

        Returns:
            A merged context with unique tables, documentation, and queries
        """
        if not contexts:
            return {}

        # Start with an empty combined context
        combined = {"relevant_tables": [], "documentation": [], "queries": []}

        # Track items we've seen to avoid duplicates
        seen_tables = set()
        seen_docs = set()
        seen_queries = set()

        # Process each context object
        for context in contexts:
            # Add unique tables
            for table in context.get("relevant_tables", []):
                table_name = table.get("name", "")
                if table_name and table_name not in seen_tables:
                    combined["relevant_tables"].append(table)
                    seen_tables.add(table_name)

            # Add unique documentation
            for doc in context.get("documentation", []):
                doc_title = doc.get("title", "")
                if doc_title and doc_title not in seen_docs:
                    combined["documentation"].append(doc)
                    seen_docs.add(doc_title)

            # Add unique queries
            for query in context.get("queries", []):
                query_title = query.get("title", "")
                if query_title and query_title not in seen_queries:
                    combined["queries"].append(query)
                    seen_queries.add(query_title)

        # Remove empty keys
        return {k: v for k, v in combined.items() if v}

    def generate_answer(
        self,
        question: str,
        current_context: Dict[str, Any],
        conversation_history: List[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate an answer using the LLM based on the question, current context, and conversation history.

        Args:
            question: The user's question
            current_context: Raw context data from Alation for the current question
            conversation_history: Optional list of previous Q&A pairs with their contexts
        """
        # Create system prompt
        system_prompt = """
        You are AlationGPT, an AI assistant specialized in answering questions about data in data catalog.
        
        You have been provided with context information from an Alation Data Catalog, including both current
        context for the present question and historical context from previous questions when available.
        
        Use ALL the context provided to answer the user's question accurately and concisely. The context 
        is provided as a JSON object that may contain information about tables, columns, documentation, and 
        SQL queries.
        
        The context may include these key components:
        - "relevant_tables": List of tables with their metadata and columns
        - "documentation": List of documentation articles or guides
        - "queries": List of SQL queries stored in the catalog
        
        Guidelines:
        1. Only answer based on the provided context - don't make up information
        2. If the context doesn't have enough information to answer, say so clearly
        3. For table-related questions, include relevant column information if available
        4. Be specific and precise, citing table and column names accurately
        5. When suggesting SQL, ensure it's compatible with the tables/columns in the context
        6. IMPORTANT: Use information from both current and historical context to give complete answers
        7. For follow-up questions, reference information from previous exchanges
        
        Format your answers in a clear, structured way with headings and bullet points when appropriate.
        """

        messages = [{"role": "system", "content": system_prompt}]

        # Prepare contextual information
        all_contexts = []

        # Add historical context from conversation history if available
        if conversation_history:
            historical_context_str = "HISTORICAL CONTEXT:\n"

            for i, entry in enumerate(conversation_history, 1):
                # Add the question and answer to messages for conversation flow
                messages.append({"role": "user", "content": entry["question"]})
                messages.append({"role": "assistant", "content": entry["answer"]})

                # Add the context to our collection for combining
                if "context" in entry:
                    all_contexts.append(entry["context"])

                    # Also add a note about this context for the LLM's reference
                    historical_context_str += (
                        f"Context {i} from question: \"{entry['question']}\"\n"
                    )

            # Provide a note about historical context being available
            if all_contexts:
                messages.append({"role": "system", "content": historical_context_str})

        # Add current context
        all_contexts.append(current_context)

        # Combine all contexts
        combined_context = self.combine_contexts(all_contexts)

        # Convert the context dict to a formatted JSON string
        context_json = json.dumps(combined_context, indent=2)

        # Add current question with combined context
        user_prompt = f"""
        Question: {question}
        
        Context from Data Catalog (combined from current and previous questions):
        {context_json}
        """
        messages.append({"role": "user", "content": user_prompt})

        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.1,  # Lower temperature for more focused answers
            max_tokens=1000,
        )

        return response.choices[0].message.content.strip()

    def answer_question(self, question: str, use_conversation_history: bool = False) -> str:
        """
        Main method to answer a question about the data catalog.

        Args:
            question: The user's question
            use_conversation_history: Whether to include previous conversation context
        """

        # Note: This example implementation always calls Alation for each question,
        # which may yield irrelevant results for follow-up questions. In a production
        # system, you might implement logic to detect follow-up questions and either:
        # 1. Skip the Alation call and use only previous context
        # 2. Rewrite the question to be more explicit before calling Alation
        # 3. Use a combination approach based on the specific question type

        # Step 1: Get context from Alation's LLM-powered context API
        context_data = self.get_catalog_context(question)

        # Step 2: Generate answer using the LLM with current and historical context
        history = self.conversation_history if use_conversation_history else None
        answer = self.generate_answer(question, context_data, history)

        # Step 3: Update conversation history - now including context
        self.conversation_history.append(
            {"question": question, "context": context_data, "answer": answer}
        )

        # Keep conversation history to a reasonable size
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]

        return answer


def main():
    """Entry point for the QA application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Data Catalog QA Bot")
    parser.add_argument("--question", "-q", type=str, help="Question to ask about the data catalog")
    parser.add_argument(
        "--conversation",
        "-c",
        action="store_true",
        help="Enable conversation mode (maintain context between questions)",
    )
    args = parser.parse_args()

    try:
        # Initialize QA system
        qa_system = DataCatalogQA()

        if args.question:
            # Answer the provided question
            question = args.question
            answer = qa_system.answer_question(question, args.conversation)

            print(f"\nQ: {question}\n")
            print(f"A: {answer}\n")
        else:
            # Interactive mode
            print("\nData Catalog QA Bot")
            if args.conversation:
                print("Conversation mode enabled - context will be maintained between questions.")
            print("Type 'exit' to quit.\n")

            while True:
                # Get user question
                question = input("Ask a question: ").strip()

                if question.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye!")
                    break

                if not question:
                    continue

                # Get answer
                print("\nThinking...\n")
                answer = qa_system.answer_question(question, args.conversation)

                print(f"Answer:\n{answer}\n")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
