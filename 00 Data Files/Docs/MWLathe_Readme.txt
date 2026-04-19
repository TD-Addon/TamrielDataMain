ID replacement tool for Morrowind.

For updates and Linux/MacOS binaries visit https://github.com/KnobelKnight/MWLathe

Replaces IDs in all contexts, including scripts and dialogue results.

Usage: mwlathe.exe <input.esm/esp> <output.esm/esp> <ID map file>

For ID map: <old ID>,<new ID>

Make sure ID map is headerless and without quotes!

Options:

-s <separator> | Set custom separator for id_map. Mandatory for non-csv/tsv files

-b | Replace IDs within book texts. Useful for ex. PositionCell markers, but unsafe with plaintext IDs

-p <changelog file> | Print a list of all affected objects to changelog file in tab-separated format

Example command:
./MWLathe.exe "..\TR_Mainland.esm" "..\TR_Mainland-patched.esm" Translation.txt -s : -p lathe_changelog.txt