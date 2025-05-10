import os

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from alation_ai_agent_langchain import AlationAIAgentSDK, get_langchain_tools

# Ignore warnings of print() usage
# ruff: noqa: T201

# Load credentials from env
base_url = os.getenv("ALATION_BASE_URL")
user_id = os.getenv("ALATION_USER_ID")
refresh_token = os.getenv("ALATION_REFRESH_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not all([base_url, user_id, refresh_token, openai_api_key]):
    value_error_message = "Missing one or more required environment variables."
    raise ValueError(value_error_message)

# Init Alation SDK
sdk = AlationAIAgentSDK(base_url=base_url, user_id=int(user_id), refresh_token=refresh_token)

# LangChain tools
tools = get_langchain_tools(sdk)

# Define a simpler prompt that doesn't require explicit tool variables
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant using Alation's metadata catalog."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# LLM (OpenAI)
llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=openai_api_key)

# Create agent using OpenAI functions approach - handles tool formatting internally
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

# Agent executor
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
)

# Example 1: Without signature
print("\n=== Example 1: Without Signature ===")
question = "What are the sales tables in our data warehouse?"
response = executor.invoke(
    {
        "input": question,
    }
)
print("\nAgent Response (Without Signature):")
print(response)

# Example 2: With signature
print("\n=== Example 2: With Signature ===")
tables_only_signature = {"table": {"fields_required": ["name", "title", "description", "url"]}}
qa_question = "What tables contain sales data?"
qa_response = executor.invoke(
    {
        "input": qa_question,
        "signature": tables_only_signature,
    }
)
print("\nAgent Response (With Signature):")
print(qa_response)
