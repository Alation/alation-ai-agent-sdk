# Multi-Agent Return Eligibility System with Alation AI Agent SDK

> **IMPORTANT**: This repository contains example code intended for educational and demonstration purposes only. It is not production-ready code. The intended audience is application developers who want to learn how to integrate Alation AI Agent SDK with LangChain to build multi-agent systems.

This example demonstrates how to build a modular multi-agent system using the Alation AI Agent SDK and LangChain to handle product return requests for an e-commerce customer service application.

## Overview

The system uses specialized agents that collaborate to identify customers, retrieve relevant purchase information, and determine return eligibility based on company policies. The example showcases how to use the Alation catalog as a knowledge source for contextual information and decision-making.

## Agents

The system consists of three specialized agents:
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Identification  │     │ Context         │     │ Eligibility     │
│ Agent           │──▶  │ Agent           │──▶  │ Agent           │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Customer Profile│     │ • Purchase      │     │ Category-based  │
│ data            │     │   History       │     │ Return Policies │
│                 │     │ • Membership    │     │ + Eligibility   │
│                 │     │ • Warranties    │     │   Rules         │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```
Each agent accesses specific information from the Alation catalog to make informed decisions, creating a modular workflow that effectively processes customer return requests.

### 1. User Identification Agent (`user_identification.py`)
- **Purpose**: Identifies customers based on email or natural language query
- **Process**:
  1. Uses Alation context tool to understand customer profile schema
  2. Forms and executes appropriate SQL queries to find the customer
  3. Returns structured customer information

### 2. Context Agent (`customer_context.py`)
- **Purpose**: Determines which data is relevant and retrieves it
- **Process**:
  1. Analyzes the customer query to determine which tables are relevant
  2. Uses Alation context to get metadata about selected tables
  3. Executes SQL queries to fetch relevant customer data
  4. Organizes context for the eligibility agent

### 3. Eligibility Agent (`eligibility.py`)
- **Purpose**: Makes the final return eligibility decision
- **Process**:
  1. Uses Alation context to retrieve relevant return policies
  2. Analyzes purchase information against policies
  3. Provides eligibility decision with detailed reasoning
  4. Generates customer-friendly response

## Setup & Installation

### Prerequisites
- Python 3.10+
- A valid API Access Token created on your Alation Data Catalog instance
- OpenAPI API Key

### Installation Steps

1. Navigate to the folder:
   ```bash
   cd multi_agent_return_eligibility
   ```

2. Create a virtual environment:
   ```bash
   # Using venv
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Duplicate `.env.example` file to `.env` in the root directory and update it.

## Running the Example

This project provides two ways to run the system:

### 1. Test Script with Multiple Scenarios

The `run_customer_service_test.py` script demonstrates the system's capabilities through several pre-defined test cases covering different eligibility scenarios. This is recommended for seeing the agents in action across a range of situations.

```bash
python run_customer_service_test.py
```


### 2. Interactive CLI Application

The `run.py` script provides an interactive command-line interface using a LangGraph workflow implementation. This impementation allows you to test the system with your own queries.

```bash
python run.py
```

## Notes and Limitations

- This example uses SQLite for simplicity; in production, you would connect to your actual database
- Mock implementations are provided for development without a live Alation instance
- The agents are designed for demonstration purposes and may need additional error handling and edge case management for production use
- You may need to tune agent prompts and LLM parameters for optimal performance in your environment

## Further Resources

- [Alation AI Agent SDK Documentation](https://github.com/Alation/ai-agent-sdk)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Anthropic's Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- [Model Context Protocol Guide](https://github.com/Alation/ai-agent-sdk/blob/main/guides/mcp/readme.md)

---