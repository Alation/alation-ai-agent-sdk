# Tool Management

### Background

Extending LLM capabilities with tools can result in extraordinary feats.

You'd think adding even more tools would continue improving what the LLM can do, right? This is true to a point then diminishing returns take over.

LLMs run into trouble when given too many tools. While exact limits are debatable it is best to track the number and understand the purpose of each tool.

### Context Overload
<details>
<summary>Expand description</summary>
<br>
Lengthy tool descriptions are common place for a few reasons. For instance, descriptions must describe what a tool is capable of.  And the best descriptions contain usage examples. Each tool takes a chunk out of the context window.  At larger sizes LLMs may hallucinate impacting accuracy. Frontier models suffer less from this than earlier but it's still a good idea to only load what you need.
</details>

### Tool belt vs Tool chest
<details>
<summary>Expand description</summary>
<br>
<p>
Using fewer tools makes it's easier to identify and communicate the one you need. Imagine a friend helping you with a small home improvement project where they wear a tool belt. Let's assume they have a hammer, two screwdrivers (Flat Head, Phillips), and a tape measure. It should be pretty straightforward for you to ask for a particular tool. While there may be some ambiguity with the screwdrivers, there are only two to choose from.</p>

<p>Now imagine your friend is in charge of an entire tool chest. Getting the right tool can be painful if the language used to request them isn't precise. Say you asked for a screwdriver and now instead of two to choose from there are twelve. One in twelve aren't great odds.</p>

<p>LLMs suffer the same issue when there are many tools that overlap in purpose. It's possible to use them but they need detailed instructions. Ambiguous cases may result in the LLM picking the wrong tool. Nobody enjoys writing verbose instructions on a routine basis. That affects the ergonomics of chatbot usage and even agent development.</p>
</details>

### Tools specific to User Role
<details>
<summary>Expand description</summary>
<br>
<p>
Some tools use APIs that require a specific user role like Server Admin or Catalog Admin to function.</p>

<p>Enforcing these permissions is important to maintaining the integrity of the catalog. At the same time, users may see these tools as enabled or available despite not being able to use them. This can lead to mismatched expectations despite there being no risk.</p>

<p>Ideally the only tools listed are the ones users can actually use.</p>
</details>

### Tool Selection

The good news is you likely already have the ability to enable or disable a tool if you're using an MCP client. But if you aren't, you may want to disable specific tools that may otherwise conflict. Follow the examples below to see how you can disable tools as needed.

### Enabling Beta Tools

You may want to take advantage of a new feature that hasn't hit GA yet. Beta tools aren't enabled by default so they need an opt-in. The follow are tools in Beta:
- `AlationTools.LINEAGE` or `lineage`

> **IMPORTANT:** Certain features must be enabled on the Alation instance. Enabling a beta tool within the SDK won't change your Alation instance's settings.

## Examples

### Local MCP Server

#### Command Line Arguments (recommended)

Command line arguments are the best, most explicit, way to control tools. Command line arguments make executions reproducible. As a bonus they show up in process lists and persist in your shell history.

```bash
python -m alation_ai_agent_mcp --disabled-tools="update_metadata,generate_data_product" --enabled-beta-tools="lineage"
```

#### Environment Variables

You can use environment variables to achieve the same result. We recommend against them as they are not as visible and easy to forget.

```bash
export ALATION_DISABLED_TOOLS="update_metadata,generate_data_product"
export ALATION_ENABLED_BETA_TOOLS="lineage"

python -m alation_ai_agent_mcp
```


### Code

You may use the `disabled_tools` or `enabled_beta_tools` kwarg to pass a set of `AlationTools` items into `AlationAIAgentSDK`.

```python
from alation_ai_agent_sdk import AlationAIAgentSDK, AlationTools
from alation_ai_agent_sdk.api import AuthParams

base_url = "https://your-instance.alationcorp.com"

sdk = AlationAIAgentSDK(
    base_url=base_url,
    auth_method="service_account",
    auth_params=AuthParams(
        client_id="you-client-id",
        client_secret="your-client-secret",
    ),
    disabled_tools={AlationTools.UPDATE_METADATA}
    enabled_beta_tools={AlationTools.LINEAGE}
)
# returns default tools without UPDATE_METADATA and with the LINEAGE beta tool
sdk.get_tools()
```



