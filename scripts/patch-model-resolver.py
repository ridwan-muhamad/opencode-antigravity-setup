#!/usr/bin/env python3
"""
patch-model-resolver.py
Applies compatibility enhancements to the installed opencode-antigravity-auth plugin:
1. Auto-redirects deprecated 'gemini-3-pro' requests to 'gemini-3.1-pro'
2. Enables 'antigravity-gemini-3.8-flash' mapping to 'gemini-3-flash'
"""

import os
import glob
import sys

def patch_file(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # 1. Patch resolveModelWithTier
    target = 'let modelWithoutQuota = requestedModel.replace(QUOTA_PREFIX_REGEX, "");'
    if target not in content and 'const modelWithoutQuota = requestedModel.replace(QUOTA_PREFIX_REGEX, "");' in content:
        content = content.replace(
            'const modelWithoutQuota = requestedModel.replace(QUOTA_PREFIX_REGEX, "");',
            target
        )
        modified = True

    replacement = (
        '    let modelWithoutQuota = requestedModel.replace(QUOTA_PREFIX_REGEX, "");\n'
        '    if (/^gemini-3-pro/i.test(modelWithoutQuota)) {\n'
        '        modelWithoutQuota = modelWithoutQuota.replace(/^gemini-3-pro/i, "gemini-3.1-pro");\n'
        '    }\n'
        '    if (/^gemini-3(?:\\.\\d+)?-flash/i.test(modelWithoutQuota)) {\n'
        '        modelWithoutQuota = modelWithoutQuota.replace(/^gemini-3(?:\\.\\d+)?-flash/i, "gemini-3-flash");\n'
        '    }'
    )

    if target in content and 'gemini-3.1-pro' not in content:
        content = content.replace(target, replacement)
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Berhasil mem-patch: {filepath}")
        return True
    else:
        print(f"[*] Sudah di-patch sebelumnya atau format berbeda: {filepath}")
        return False

def main():
    home = os.path.expanduser("~")
    search_patterns = [
        os.path.join(home, ".cache/opencode/packages/**/model-resolver.js"),
        os.path.join(home, ".opencode/**/model-resolver.js"),
        os.path.join(home, ".config/opencode/**/model-resolver.js"),
    ]

    found = []
    for pattern in search_patterns:
        for p in glob.glob(pattern, recursive=True):
            if "dist/src/plugin/transform/model-resolver.js" in p:
                found.append(p)

    if not found:
        print("[-] File model-resolver.js plugin tidak ditemukan di direktori cache OpenCode.")
        print("    Pastikan Anda sudah menginstall plugin terlebih dahulu via: opencode plugin opencode-antigravity-auth@latest")
        sys.exit(1)

    for path in set(found):
        patch_file(path)

if __name__ == "__main__":
    main()
