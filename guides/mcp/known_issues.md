# MCP Known Issues

This document outlines known issues and their solutions when working with Alation MCP (Model Context Protocol) integrations.

## SSL Certificate Issues with Corporate VPNs

### Issue Description
When using the MCP Inspector with corporate VPNs (particularly Zscaler), you may encounter SSL certificate errors that prevent connections to MCP servers.

**Error Message:**
```
Error from MCP server: TypeError: fetch failed
    at node:internal/deps/undici/undici:13185:13
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async StreamableHTTPClientTransport.send (file:///Users/jags.saragadam/.npm/_npx/9eac9498388ae25e/node_modules/@modelcontextprotocol/sdk/dist/esm/client/streamableHttp.js:267:30) {
  [cause]: Error: unable to get local issuer certificate
      at TLSSocket.onConnectSecure (node:_tls_wrap:1677:34)
      at TLSSocket.emit (node:events:519:28)
      at TLSSocket._finishInit (node:_tls_wrap:1076:8)
      at ssl.onhandshakedone (node:_tls_wrap:862:12) {
    code: 'UNABLE_TO_GET_ISSUER_CERT_LOCALLY'
  }
}
```

### Root Cause
Corporate VPNs like Zscaler perform SSL inspection by intercepting HTTPS connections and presenting their own certificates. Node.js applications (including MCP Inspector) cannot verify these certificates because the corporate root certificate is not in Node.js's trusted certificate store.

### Affected Tools
- MCP Inspector (`@modelcontextprotocol/inspector`)
- Any Node.js-based MCP clients
- Other development tools that make HTTPS requests through corporate VPNs

### Solutions

#### Solution 1: Temporarily Disable VPN Internet Security (Easy but Limited)
**When to use:** For quick testing when IT policies allow temporary VPN disabling.

1. Temporarily disable Zscaler Internet Security or similar VPN protection
2. Run your MCP Inspector tests
3. Re-enable VPN protection after testing

**⚠️ Limitations:**
- May be blocked by corporate IT policies
- Leaves your connection unprotected during testing
- Not suitable for ongoing development work

#### Solution 2: Configure Node.js to Trust Corporate Root Certificate (Recommended)
**When to use:** For ongoing development work or when VPN cannot be disabled.

1. **Obtain your organization's root certificate:**
   - For Zscaler: Follow [Adding Custom Certificate to Application-Specific Trust Store](https://help.zscaler.com/zia/adding-custom-certificate-application-specific-trust-store)
   - Contact your IT department if you need assistance obtaining the certificate
   - The certificate should be in `.crt` or `.pem` format

2. **Configure Node.js to use the certificate:**
   ```bash
   # Add the certificate path to your shell profile
   echo "export NODE_EXTRA_CA_CERTS=/path/to/your/corporate-root-cert.crt" >> $HOME/.zshrc
   
   # Reload your shell configuration
   source ~/.zshrc
   ```

   **Note:** Replace `/path/to/your/corporate-root-cert.crt` with the actual path to your downloaded certificate.

3. **Verify the configuration:**
   ```bash
   # Check that the environment variable is set
   echo $NODE_EXTRA_CA_CERTS
   
   # Run MCP Inspector
   npx @modelcontextprotocol/inspector@latest
   ```

#### Solution 3: Alternative Certificate Configuration (macOS/Linux)
For some environments, you may need to use a different approach:

```bash
# Alternative method using NODE_TLS_REJECT_UNAUTHORIZED (less secure)
export NODE_TLS_REJECT_UNAUTHORIZED=0

# Or add multiple certificates if needed
export NODE_EXTRA_CA_CERTS="/path/to/cert1.crt:/path/to/cert2.crt"
```

**⚠️ Security Warning:** Using `NODE_TLS_REJECT_UNAUTHORIZED=0` disables all SSL certificate verification and should only be used for testing in secure environments.

### Verification Steps

After applying a solution:

1. **Test the MCP Inspector connection:**
   ```bash
   npx @modelcontextprotocol/inspector@latest
   ```

2. **Connect to your MCP server** and verify you can:
   - See available tools
   - Execute tool calls successfully
   - Receive proper responses

3. **Check for certificate warnings** in the inspector logs

---

**Last Updated:** September 15, 2025
