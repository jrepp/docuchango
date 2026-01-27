---
title: Title Goes Here
status: Draft
author: Engineering Team  # git config user.name
created: YYYY-MM-DDTHH:MM:SSZ  # python -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))"
tags: [rfc, design]
id: rfc-000  # lowercase rfc-XXX format matching filename
project_id: my-project  # from docs-project.yaml
doc_uuid: 00000000-0000-4000-8000-000000000000  # python -c "import uuid; print(uuid.uuid4())"
---

# Summary

Brief one-paragraph explanation of the proposal.

# Motivation

Why are we doing this? What use cases does it support? What is the expected outcome?

# Detailed Design

This is the bulk of the RFC. Explain the design in enough detail for somebody familiar with the system to understand, and for somebody familiar with the code to implement.

## API Changes

If applicable, describe any API changes.

## Data Model Changes

If applicable, describe any data model changes.

## Migration Strategy

How will we migrate existing systems/data?

# Drawbacks

Why should we *not* do this? What are the costs and risks?

# Alternatives

What other designs have been considered? What is the impact of not doing this?

## Alternative 1

Description and comparison.

## Alternative 2

Description and comparison.

# Adoption Strategy

How will existing users adopt this change? Do we need documentation updates? Training?

# Unresolved Questions

What parts of the design are still TBD? What questions need to be resolved during implementation?

# Future Possibilities

What related future work might build on this RFC?
