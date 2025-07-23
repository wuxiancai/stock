# 🐍 Python 兼容性解决方案

## 问题描述

如果您遇到以下错误：
- `pip` 依赖解析失败
- `pydantic-core` 编译错误
- Python 3.13 兼容性问题

## 🚀 快速解决方案

### 方案 1：自动安装 Python 3.12（推荐）

```bash
# 1. 安装 Python 3.12
chmod +x install_python312.sh
./install_python312.sh

# 2. 运行安装脚本（会自动选择 Python 3.12）
./setup_macos.sh
```

### 方案 2：手动安装 Python 3.12

```bash
# 安装 Python 3.12
brew install python@3.12

# 验证安装
python3.12 --version

# 运行安装脚本
./setup_macos.sh
```

### 方案 3：测试当前环境

```bash
# 测试 Python 版本选择逻辑
chmod +x test_python_fix.sh
./test_python_fix.sh
```

## 🔧 修复说明

修复后的 `setup_macos.sh` 脚本现在会：

1. **智能选择 Python 版本**：
   - 优先级：3.12 > 3.11 > 3.10 > 3.9 > 3.13
   - 自动跳过有问题的 Python 3.13

2. **强制重新创建虚拟环境**：
   - 删除旧的虚拟环境
   - 使用选择的 Python 版本创建新环境
   - 验证版本匹配

3. **兼容性优化**：
   - Python 3.13：启用特殊兼容性设置
   - Python 3.12/3.11/3.10：最佳兼容性
   - 提供详细的错误信息和解决建议

## 📋 支持的 Python 版本

| 版本 | 状态 | 说明 |
|------|------|------|
| 3.12 | ✅ 推荐 | 最佳兼容性，所有包都能正常安装 |
| 3.11 | ✅ 良好 | 兼容性良好 |
| 3.10 | ✅ 良好 | 兼容性良好 |
| 3.9  | ⚠️ 可用 | 最低支持版本 |
| 3.13 | ⚠️ 问题 | 某些包存在兼容性问题 |

## 🎯 如果仍有问题

1. **清理环境**：
   ```bash
   rm -rf venv
   pip cache purge
   ```

2. **重新运行**：
   ```bash
   ./setup_macos.sh
   ```

3. **查看日志**：
   - 检查 Python 版本选择日志
   - 确认虚拟环境使用了正确的版本

## 📞 技术支持

如果问题仍然存在，请提供：
- 系统信息：`uname -a`
- Python 版本：`python3 --version`
- 错误日志的完整输出