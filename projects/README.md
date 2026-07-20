# AI CAD projects

Each directory is a persistent AI-editable CAD project. A project is a
transparent collection of text files rather than an opaque CAD document.

Required files:

- `project.json` - identity, entry point, named bodies, outputs, and workflow.
- `parameters.json` - current numeric and option values.
- `parameter_schema.json` - validation rules and parameter-editor metadata.
- `references.json` - reference provenance and trust classification.
- `validation.json` - results from the last accepted MCP validation run.
- `revisions/` - immutable revision records and parameter snapshots.

The model entry point must accept the complete parameter mapping and return a
dictionary containing stable `bodies` and `interfaces` names. STEP/STL/SVG are
derived artifacts; the project files and model source are the editable source
of truth.

User parameter edits update `parameters.json`. Semantic changes update the
model source and, when necessary, the schema. Every rebuild must pass the same
MCP validation gates before becoming the accepted project revision.
