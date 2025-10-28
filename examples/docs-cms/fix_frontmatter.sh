#!/bin/bash
set -euo pipefail

# Generate UUID function
gen_uuid() {
    uuidgen | tr '[:upper:]' '[:lower:]'
}

# Fix ADR-001
cat > adr/adr-001-adopt-docs-cms.md << 'EOF'
---
id: adr-001
title: Adopt docs-cms for Documentation Management
status: Accepted
date: 2025-10-27
deciders: Project Team
tags: [architecture, documentation, tooling]
project_id: example-project
doc_uuid: 550e8400-e29b-41d4-a716-446655440000
---
EOF

# Fix ADR-002  
cat > adr/adr-002-agent-collaboration-workflow.md << 'EOF'
---
id: adr-002
title: Define Agent Collaboration Workflow with docs-cms
status: Accepted
date: 2025-10-27
deciders: Project Team and AI Agents
tags: [architecture, ai-agents, workflow, collaboration]
project_id: example-project
doc_uuid: 7c9e6679-7425-40de-944b-e07fc1f90ae7
---
EOF

# Fix RFC-001
cat > rfcs/rfc-001-automated-doc-generation.md << 'EOF'
---
id: rfc-001
title: Automated Documentation Generation from Code
status: Draft
author: Claude Code Agent
created: 2025-10-27
updated: 2025-10-27
tags: [rfc, automation, documentation, tooling]
project_id: example-project
doc_uuid: 4a5b6c7d-8e9f-4012-8345-6789abcdef01
---
EOF

# Fix Memo-001
cat > memos/memo-001-docs-cms-launch.md << 'EOF'
---
id: memo-001
title: docs-cms System Launch Status
author: Project Team
created: 2025-10-27
updated: 2025-10-27
tags: [memo, status-update, launch]
project_id: example-project
doc_uuid: 4b5c6d7e-8f90-4123-8456-789abcdef012
---
EOF

echo "Frontmatter headers updated"
