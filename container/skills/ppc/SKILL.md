---
name: ppc
description: Web search and research tool. Executes a Python script that calls a local search API with query and conversation history. 5-minute timeout.
allowed-tools: Bash(python3:*)
---

# PPC Search Tool

Web search and research command using `/ppc`.

## Usage

```
/ppc <search query>
```

Example:
```
/ppc Claude AI assistant capabilities
```

## How It Works

1. **Extract the query**: Parse everything after `/ppc ` as the search query
   - Example: `/ppc Claude AI capabilities` → query = "Claude AI capabilities"

2. **Build conversation history**: Include only relevant history that relates to the search query
   - History format: array of [role, message] pairs where role is "human" or "assistant"
   - Only include messages that are contextually relevant to the query
   - Format as JSON string for the --history parameter

3. **Execute the search script**:
   ```bash
   cd /workspace/project/container/skills/ppc
   python3 search_request.py --query "<query>" --history '<json_history>'
   ```
   - Timeout: 5 minutes (300 seconds)
   - The script calls `http://host.docker.internal:3000/api/search`

4. **Return results**: Return the full API response to the user without summarization or any modification

## Example

- User: `/ppc What is Claude Code?`
- Extract query: "What is Claude Code?"
- Build relevant history (if any)
- Execute: `python3 search_request.py --query "What is Claude Code?" --history '[]'`
- Return the API response to the user
