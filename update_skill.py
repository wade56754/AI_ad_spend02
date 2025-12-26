#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Update SKILL.md version references"""

import os
os.chdir(r'D:\project\AI_ad_spend02')

skill_path = r'.claude\skills\ai-ad-code-factory\SKILL.md'

with open(skill_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update version references
content = content.replace('code-blocks-registry.md v1.0', 'code-blocks-registry.md v2.0')

with open(skill_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated SKILL.md version references")
