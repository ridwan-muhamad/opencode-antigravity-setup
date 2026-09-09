#!/usr/bin/env python3
"""
patch-model-resolver.py
Applies compatibility & stability enhancements to the installed opencode-antigravity-auth plugin:
1. Auto-redirects deprecated 'gemini-3-pro' requests to 'gemini-3.1-pro'
2. Enables 'antigravity-gemini-3.8-flash' mapping to 'gemini-3-flash'
3. Maps 'gemini-3.1-pro --variant=high' to 'gemini-pro-agent'
4. Locks Antigravity endpoints to Sandbox Daily to eliminate 403 (Autopush) and 429 quota exhaustion lockout (Prod)
5. Sets daily endpoint for account verification and project discovery
"""

import os
import glob
import re
import sys

def patch_model_resolver(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # 1. Patch resolveModelWithTier for model redirection (pro redirect & flash mapping)
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

    if target in content and 'replace(/^gemini-3-pro/i' not in content:
        content = content.replace(target, replacement, 1)
        modified = True

    # 2. Patch pro-high variant -> gemini-pro-agent (deprecated backend model id redirect)
    target_pro_tier = (
        '        if (isGemini3Pro && !tier && !isImageModel) {\n'
        '            antigravityModel = `${modelWithoutQuota}-low`;\n'
        '        }\n'
        '        else if (isGemini3Flash && tier) {'
    )
    replacement_pro_tier = (
        '        if (isGemini3Pro && !tier && !isImageModel) {\n'
        '            antigravityModel = `${modelWithoutQuota}-low`;\n'
        '        }\n'
        '        else if (isGemini3Pro && tier === "high") {\n'
        '            antigravityModel = "gemini-pro-agent";\n'
        '        }\n'
        '        else if (isGemini3Flash && tier) {'
    )
    if target_pro_tier in content and 'gemini-pro-agent' not in content:
        content = content.replace(target_pro_tier, replacement_pro_tier, 1)
        modified = True

    # 3. Patch resolveModelWithVariant for pro-high level -> gemini-pro-agent
    target_variant = 'actualModel = `${baseModel}-${level}`;'
    replacement_variant = 'actualModel = (level === "high") ? "gemini-pro-agent" : `${baseModel}-${level}`;'
    if target_variant in content and replacement_variant not in content:
        content = content.replace(target_variant, replacement_variant, 1)
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Berhasil mem-patch model-resolver: {filepath}")
        return True
    else:
        print(f"[*] Model-resolver sudah up-to-date: {filepath}")
        return False

def patch_constants(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # Patch ANTIGRAVITY_ENDPOINT_FALLBACKS to only use DAILY sandbox
    # This completely eliminates poisoning the account with 403 (Autopush) and 429 Quota Exhausted (Prod)
    target_fallbacks = (
        'export const ANTIGRAVITY_ENDPOINT_FALLBACKS = [\n'
        '    ANTIGRAVITY_ENDPOINT_DAILY,\n'
        '    ANTIGRAVITY_ENDPOINT_AUTOPUSH,\n'
        '    ANTIGRAVITY_ENDPOINT_PROD,\n'
        '];'
    )
    replacement_fallbacks = (
        'export const ANTIGRAVITY_ENDPOINT_FALLBACKS = [\n'
        '    ANTIGRAVITY_ENDPOINT_DAILY,\n'
        '];'
    )
    if target_fallbacks in content:
        content = content.replace(target_fallbacks, replacement_fallbacks, 1)
        modified = True

    # Patch ANTIGRAVITY_LOAD_ENDPOINTS to prioritize DAILY
    target_load = (
        'export const ANTIGRAVITY_LOAD_ENDPOINTS = [\n'
        '    ANTIGRAVITY_ENDPOINT_PROD,\n'
        '    ANTIGRAVITY_ENDPOINT_DAILY,\n'
        '    ANTIGRAVITY_ENDPOINT_AUTOPUSH,\n'
        '];'
    )
    replacement_load = (
        'export const ANTIGRAVITY_LOAD_ENDPOINTS = [\n'
        '    ANTIGRAVITY_ENDPOINT_DAILY,\n'
        '    ANTIGRAVITY_ENDPOINT_PROD,\n'
        '];'
    )
    if target_load in content:
        content = content.replace(target_load, replacement_load, 1)
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Berhasil mem-patch constants: {filepath}")
        return True
    else:
        print(f"[*] Constants sudah up-to-date: {filepath}")
        return False

def patch_plugin(filepath):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    # Ensure ANTIGRAVITY_ENDPOINT_DAILY is imported
    target_import = 'import { ANTIGRAVITY_DEFAULT_PROJECT_ID, ANTIGRAVITY_ENDPOINT_FALLBACKS, ANTIGRAVITY_ENDPOINT_PROD, ANTIGRAVITY_PROVIDER_ID, getAntigravityHeaders, } from "./constants";'
    replacement_import = 'import { ANTIGRAVITY_DEFAULT_PROJECT_ID, ANTIGRAVITY_ENDPOINT_FALLBACKS, ANTIGRAVITY_ENDPOINT_DAILY, ANTIGRAVITY_ENDPOINT_PROD, ANTIGRAVITY_PROVIDER_ID, getAntigravityHeaders, } from "./constants";'
    if target_import in content:
        content = content.replace(target_import, replacement_import, 1)
        modified = True

    # Patch verifyAccountQuota to check DAILY sandbox instead of PROD (which returns 429)
    target_verify = 'response = await fetch(`${ANTIGRAVITY_ENDPOINT_PROD}/v1internal:streamGenerateContent?alt=sse`,'
    replacement_verify = 'response = await fetch(`${ANTIGRAVITY_ENDPOINT_DAILY}/v1internal:streamGenerateContent?alt=sse`,'
    if target_verify in content:
        content = content.replace(target_verify, replacement_verify, 1)
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] Berhasil mem-patch plugin: {filepath}")
        return True
    else:
        print(f"[*] Plugin sudah up-to-date: {filepath}")
        return False

def main():
    home = os.path.expanduser("~")
    search_dirs = [
        os.path.join(home, ".cache/opencode/packages"),
        os.path.join(home, ".opencode"),
        os.path.join(home, ".config/opencode"),
    ]

    found_mr = []
    found_const = []
    found_plugin = []

    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for p in glob.glob(os.path.join(sdir, "**/model-resolver.js"), recursive=True):
            if "dist/src/plugin/transform/model-resolver.js" in p:
                found_mr.append(p)
        for p in glob.glob(os.path.join(sdir, "**/constants.js"), recursive=True):
            if "node_modules/opencode-antigravity-auth/dist/src/constants.js" in p:
                found_const.append(p)
        for p in glob.glob(os.path.join(sdir, "**/plugin.js"), recursive=True):
            if "node_modules/opencode-antigravity-auth/dist/src/plugin.js" in p:
                found_plugin.append(p)

    if not found_mr and not found_const:
        print("[-] File plugin opencode-antigravity-auth tidak ditemukan di cache.")
        print("    Jalankan: opencode plugin opencode-antigravity-auth@latest")
        sys.exit(1)

    for path in set(found_mr):
        patch_model_resolver(path)

    for path in set(found_const):
        patch_constants(path)

    for path in set(found_plugin):
        patch_plugin(path)

if __name__ == "__main__":
    main()
