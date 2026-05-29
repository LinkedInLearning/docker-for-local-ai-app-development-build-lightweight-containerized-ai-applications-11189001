"""Chapter 5 · Lessons 4–5 — tiny demo app for the buildx / publishing demos.

It prints the CPU architecture it is running on. That is the whole point: when
we build this image for multiple platforms and run each one, the architecture in
the output changes (x86_64 vs aarch64) — proof that buildx produced the right
binary for each platform.

No third-party dependencies, so it builds in seconds and works on every
architecture — which keeps the multi-platform build and the registry push fast
and reliable to record.
"""

import platform

print(
    f"rag-demo · running on {platform.machine()} "
    f"({platform.system()} {platform.release()})"
)
