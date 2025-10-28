# Data Product Creation Example

This example demonstrates how to automatically create Alation Data Products by gathering context from your catalog and generating YAML specifications using OpenAI GPT-4o.

## Overview

The script follows a simple 3-step approach:
1. **Fetch context** from your Alation catalog using bulk retrieval
2. **Get schema instructions** from your Alation instance 
3. **Generate data product YAML** using OpenAI GPT-4o

This is just a simple example to get you started or show how it can be done. Creating a data product cannot be done in single step. The app developer needs to iterate to get to an efficient data product

## Prerequisites

- Python 3.10 or higher
- Access to an Alation Data Catalog instance
- OpenAI API key
- Valid Alation authentication credentials

## Setup

1. Install the required packages:

```bash
pip install -r requirements.txt
```

2. Set up your environment variables:

```bash
# Alation credentials
export ALATION_BASE_URL="https://your-alation-instance.com"
export ALATION_AUTH_METHOD="service_account"

# For service account authentication (recommended)
export ALATION_CLIENT_ID="your-client-id"
export ALATION_CLIENT_SECRET="your-client-secret"

# For user account authentication
export ALATION_USER_ID="your-user-id"
export ALATION_REFRESH_TOKEN="your-refresh-token"

# OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"
```

## Usage

### Basic Usage

Create a data product by filtering on domain IDs:

```bash
python data_product_generation.py --domain_ids "191" --product_name "Sales Analytics"
```

## Output

The script will generate a complete Alation Data Product YAML specification based on:
- Tables found in the specified domains
- Column information and relationships
- SQL query patterns for business context
- Current Alation Data Product schema

## Example Output

```yaml
product:
  productId: "analytics.sales_domain"
  version: "1.0"
  contactEmail: "TBD"
  contactName: "TBD"
  en:
    name: "Sales Analytics"
    description: "Comprehensive sales data product..."
  
  deliverySystems:
    production:
      type: sql
      uri: "TBD"
  
  recordSets:
    sales_table:
      name: "sales_table"
      displayName: "Sales Table"
      description: "Main sales transaction data"
      schema:
        - name: "sale_id"
          displayName: "Sale ID"
          type: "integer"
          description: "Unique identifier for each sale"
        # ... more columns
```
