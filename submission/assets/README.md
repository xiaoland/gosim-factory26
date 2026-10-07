# Public process reaper

`tini-static-amd64` is the upstream Tini v0.19.0 static amd64 artifact,
downloaded from the GitHub release and shipped as a package input. SHA-256:
`c5b0666b4cb676901f90dfcb37106783c5fe2077b04590973b885950611b30ee`.
It is MIT-licensed by the Tini project. The public entry uses `tini -s` as a
subreaper before installing Node/npm dependencies or starting the variant;
browser binaries remain an on-demand writable-cache concern.
