# Planning and Integration

To get the most out of the SDK it's important to maximize the content in the Alation Data Catalog for your agents. Review the next sections to determine how you'd like to leverage it via signatures.

### Decide which objects should be used

Consider which objects, of potentially millions in your data catalog, are most relevant to your use case(s). By default the SDK will consider the entire catalog making it useful for a general purpose Q+A chatbot.

If your agent specializes in a particular business unit or narrower area you'll want to define which slice of the catalog is used. For instance you may wish to restrict results to objects to a certain type, those with a particular tag or those found within one or more data domains.

If your catalog follows a medallion architecture you should determine which layer (bronze, silver, gold) you'd like to expose. These may be identified with a particular custom field value, a tag, or a trust flag. It's possible your organization has defined it another way. Please consult your catalog for examples in how these layers are distinguished.

### Decide which object fields are needed

Field selection ensures your agent has the right context in order to achieve the correct result. Beyond electing which fields should be included, it offers a chance to more precisely control what is in, or out of, context. Omitting extraneous fields reduces LLM token usage which saves money, speeds up responses, and reduces hallucinations.

We recommend starting the default fields then extending them as your use case(s) warrants. For more predicable results consider limiting any optional fields.

See [Using Signatures](./signature.md) for how to put these integration ideas into practice.

## Authentication

The Alation AI Agent SDK supports two authentication methods:

1. **User Account Authentication**: Ideal for personal agents. Requires a refresh token and user ID. Refer to the [Authentication Guide](./authentication.md) for setup instructions.

2. **Service Account Authentication**: Designed for shared agents. Requires a client ID and client secret. Refer to the [Authentication Guide](./authentication.md) for setup instructions.