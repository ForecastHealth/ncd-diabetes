# Modular composition

This directory owns the graph-style Botech module artefacts for this model. The component files contain Botech nodes and links; the composition manifest and link contracts describe how those components are recomposed into `composed.model.json`.

The NCD client treats this directory as the source for its generated cache under `public/models/<model>/modular-composition`, `public/models/<model>/composed.model.json`, and `state/modular-compositions/<model>`. Do not edit the client cache as the source of truth.

The older `build/components` directory, where present, contains scenario parameter bundles. Those files are not graph-style Botech modules.
