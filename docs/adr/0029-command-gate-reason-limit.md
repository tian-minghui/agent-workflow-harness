# Command gate reason limit

A failed command gate will use at most the last 1,500 Unicode characters of combined stdout/stderr, after stripping ANSI escape sequences and trailing whitespace. If the excerpt is truncated, it will begin with `...`; empty output becomes `Command failed with no output`. The CLI will never truncate by bytes, which could corrupt multibyte log text.
