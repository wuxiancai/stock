#!/usr/bin/env python3
"""
SQLAlchemy Decimal 修复脚本
将 models.py 文件中的所有 Decimal 替换为 Numeric
"""

import re

def fix_sqlalchemy_decimal():
    file_path = "/Users/wuxiancai/stock/app/database/models.py"
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换所有的 Decimal( 为 Numeric(
        content = re.sub(r'Decimal\(', 'Numeric(', content)
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ SQLAlchemy Decimal 修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    fix_sqlalchemy_decimal()