# 股票选股系统部署指南

## 概述

本文档介绍如何使用一键部署脚本将股票选股系统部署到Ubuntu云服务器。

## 部署前准备

### 1. 服务器要求
- 操作系统：Ubuntu 18.04+ 
- 内存：至少2GB
- 磁盘空间：至少5GB
- Python版本：3.6+

### 2. 上传代码
将项目代码上传到服务器的 `$HOME/stock` 目录：
```bash
# 方法1：使用git克隆
git clone <your-repo-url> ~/stock

# 方法2：使用scp上传
scp -r ./stock user@server-ip:~/

# 方法3：使用rsync同步
rsync -avz ./stock/ user@server-ip:~/stock/
```

## 部署步骤

### 1. 执行部署脚本
```bash
cd ~/stock
chmod +x deploy.sh
./deploy.sh
```

### 2. 部署过程
脚本将自动执行以下步骤：
1. ✅ 更新系统包
2. ✅ 创建Python虚拟环境
3. ✅ 安装项目依赖
4. ✅ 创建systemd服务配置
5. ✅ 安装并启动系统服务
6. ✅ 检查服务状态
7. ✅ 配置防火墙
8. ✅ 显示部署信息

### 3. 验证部署
部署完成后，访问：`http://服务器IP:8888`

## 服务管理

### 常用命令
```bash
# 查看服务状态
sudo systemctl status run-stock

# 启动服务
sudo systemctl start run-stock

# 停止服务
sudo systemctl stop run-stock

# 重启服务
sudo systemctl restart run-stock

# 查看实时日志
sudo journalctl -u run-stock -f

# 查看错误日志
sudo journalctl -u run-stock --since today
```

### 服务配置
- 服务名称：`run-stock`
- 配置文件：`/etc/systemd/system/run-stock.service`
- 工作目录：`$HOME/stock`
- 虚拟环境：`$HOME/stock-venv`
- 运行端口：`8888`

## 目录结构

```
$HOME/
├── stock/                 # 应用目录
│   ├── app.py            # 主程序
│   ├── requirements.txt  # 依赖包列表
│   ├── deploy.sh         # 部署脚本
│   ├── run-stock.service # 服务配置模板
│   └── ...               # 其他项目文件
└── stock-venv/           # Python虚拟环境
    ├── bin/
    ├── lib/
    └── ...
```

## 故障排除

### 1. 服务启动失败
```bash
# 查看详细错误信息
sudo journalctl -u run-stock --since "10 minutes ago"

# 检查服务配置
sudo systemctl cat run-stock

# 手动测试启动
cd ~/stock
source ~/stock-venv/bin/activate
python app.py
```

### 2. 端口访问问题
```bash
# 检查端口是否监听
sudo netstat -tlnp | grep 8888

# 检查防火墙状态
sudo ufw status

# 开放端口
sudo ufw allow 8888
```

### 3. 依赖包问题
```bash
# 重新安装依赖
cd ~/stock
source ~/stock-venv/bin/activate
pip install -r requirements.txt
```

### 4. 权限问题
```bash
# 检查文件权限
ls -la ~/stock/

# 修复权限
chmod +x ~/stock/deploy.sh
chown -R $USER:$USER ~/stock/
```

## 更新部署

当需要更新代码时：

```bash
# 1. 停止服务
sudo systemctl stop run-stock

# 2. 更新代码
cd ~/stock
git pull  # 或重新上传代码

# 3. 更新依赖（如果需要）
source ~/stock-venv/bin/activate
pip install -r requirements.txt

# 4. 重启服务
sudo systemctl start run-stock
```

## 卸载

如需完全卸载系统：

```bash
# 1. 停止并禁用服务
sudo systemctl stop run-stock
sudo systemctl disable run-stock

# 2. 删除服务文件
sudo rm /etc/systemd/system/run-stock.service
sudo systemctl daemon-reload

# 3. 删除应用文件
rm -rf ~/stock
rm -rf ~/stock-venv

# 4. 关闭防火墙端口（可选）
sudo ufw delete allow 8888
```

## 技术支持

如遇到问题，请提供以下信息：
1. 服务器系统版本：`lsb_release -a`
2. Python版本：`python3 --version`
3. 服务状态：`sudo systemctl status run-stock`
4. 错误日志：`sudo journalctl -u run-stock --since today`

---

**注意事项：**
- 确保服务器有足够的内存和磁盘空间
- 定期备份数据库文件
- 建议使用非root用户运行服务
- 生产环境建议配置SSL证书和域名