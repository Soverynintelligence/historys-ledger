# Sources

One file per document, named `<id>.md`. The `id` is assigned by hand and must
match the filename.

A record may carry document text **only** if `tools/fetch_source.py` retrieved
it from a URL. `tools/provenance_gate.py` enforces this. If we cannot fetch a
document, the record exists without text and the chapter keeps its citation —
a missing document is honest, a remembered one is not.

`rights: restricted` records never carry text. Today that is the two 1963 King
Estate sources in chapter 5.
