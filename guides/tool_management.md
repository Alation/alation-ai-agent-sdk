# Tool Management

### Background

Extending LLM capabilities through tool use can result in extraordinary feats previously thought impossible.

You'd think adding even more tools continues to improve what the LLM can do, right? Unfortunately this is only true to a point where beyond that diminishing returns take over.

It's been documented that LLMs run into trouble when given too many tools. While the exact limits are debatable, and may vary from one model to the next, it is a best practice to keep an eye on the overall number AND to understand the purpose of each tool.


### Context Overload
<details>
<summary>Expand description</summary>
<br>
One issue relates to tools providing lengthy descriptions for what they do, when they should be used, along with documenting example usage. Each registered tool takes a chunk out of the context window. It's been shown that as context length increases accuracy plateaus before it drops off as LLMs start to hallucinate. Frontier models suffer less from this than before but it's still a good idea to only load what you need.
</details>

### Tool belt vs Tool chest
<details>
<summary>Expand description</summary>
<br>
<p>
When tools are limited it's easier to identify and communicate the one you need. Imagine a friend helping you with a small home improvement project where they wear a tool belt. Perhaps they have a hammer, two screwdrivers (flat, phillips), and a tape measure. It should be pretty straightfoward for you to ask for a particular tool. While there may be some ambiguity with the screwdrivers, there are only two to choose from.</p>
<p>If we contrast that to a case where your friend is in charge of a tool chest, results can be comically bad if the language used to request them isn't precise. Say you asked for a screwdriver and now instead of two to choose from there are twelve. One in twelve aren't great odds.</p>
<p>
LLMs can be placed in the same situation when there are many tools that overlap in their purpose. They can be used correctly when given detailed enough instructions but when it is ambiguous the LLM might simply pick the wrong tool. And frankly speaking, nobody enjoys writing verbose instructions on a routine basis. That affects the ergonomics of chatbot usage and even agent development.</p>
</details>

### Tools specific to User Role
<details>
<summary>Expand description</summary>
<br>
<p>
Certain tools may have API implementations that require a specific user role like Server Admin or Catalog Admin to function correctly.</p>

<p>Enforcing these permissions is important to maintaining the integrity of the catalog. At the same time, users may see these tools as enabled or available despite not being able to use them. This can lead to mismatched expectations despite there being no risk.</p>

<p>This is something we'd like to improve by introspecting users accounts and filtering tools down to only those they can actualy use.</p>
</details>

### Tool Selection

The good news is you likely already have the ability to enable or disable a tool if you're using an MCP client. But if you aren't, you may want to disable specific tools that may otherwise conflict. Follow the examples below to see how you can disable tools as needed.

### Enabling Beta Tools

There may be times where you'd like to take advantage of a new feature that hasn't hit GA yet or if there is an experiemental tool you'd like to try. Beta tools aren't enabled by default and require an explict opt-in to make use of.

<blockquote>
IMPORTANT: While you can enable a beta tool within the SDK it's important to understand your Alation instance may need the appropriate feature flags enabled before the corresponding tool calls will work.
</blockquote>


## Examples

### Local MCP Server

#### Command Line Arguments (recommended)

Command line arguments are the most explicit way to achieve this effect and make it consistently reproducible. Executed commands are introspectable in the process list and get added to your history where they can be referenced later.

```bash
python -m alation_ai_agent_mcp --disabled-tools="update_metadata,generate_data_product" --enabled-beta-tools="lineage"
```

#### Environment Variables

You can use environment variables to achieve the same result. We recommend CLI arguments as env variables can frequently be overlooked and may not be set etc.

```bash
export ALATION_DISABLED_TOOLS="update_metadata,generate_data_product"
export ALATION_ENABLED_BETA_TOOLS="lineage"

python -m alation_ai_agent_mcp
```


### Code

If you're using `alation-ai-agent-sdk` and are instantiating `AlationAIAgentSDK` you may use either the `disabled_tools` or `enabled_beta_tools` kwarg to pass a set of `AlationTools` items.

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



