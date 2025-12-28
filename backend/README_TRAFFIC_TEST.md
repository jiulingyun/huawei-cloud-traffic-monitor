# 流量包查询服务测试指南

## 测试脚本

`test_traffic_service.py` 支持两种测试模式：

### 1. 离线测试模式（默认）

使用模拟数据测试服务逻辑，无需真实 API 凭证。

```bash
# 直接运行
python test_traffic_service.py

# 或使用 venv
../backend/venv/bin/python test_traffic_service.py
```

**测试内容：**
- ✅ TrafficPackage 数据模型解析
- ✅ TrafficService 服务初始化
- ✅ API 响应解析逻辑
- ✅ 流量汇总计算
- ✅ 阈值检查逻辑

### 2. 真实联调模式

使用真实华为云 API 凭证进行联调测试。

#### 步骤 1: 设置环境变量

```bash
# 必需：华为云 AK/SK
export HUAWEI_AK="your_access_key_here"
export HUAWEI_SK="your_secret_key_here"

# 必需：流量包 ID 列表（逗号分隔）
export TRAFFIC_RESOURCE_IDS="fr-xxxxxxxxxxxxxxxx,fr-yyyyyyyyyyyyyyyy"

# 可选：区域（默认 cn-north-4）
export HUAWEI_REGION="cn-north-4"
```

#### 步骤 2: 运行真实测试

```bash
python test_traffic_service.py --real
```

**测试内容：**
- 🔍 测试 1: 查询流量包详情（显示每个流量包的完整信息）
- 🔍 测试 2: 获取总剩余流量
- 🔍 测试 3: 获取流量汇总（包含统计信息）
- 🔍 测试 4: 检查流量阈值（默认阈值 100GB）

#### 步骤 3: 查看测试结果

成功示例输出：

```
配置信息：
   AK: ABCD****WXYZ
   Region: cn-north-4
   流量包数量: 2
   流量包ID: fr-xxx, fr-yyy

✅ 客户端创建成功
✅ 流量服务初始化成功

🔍 测试 1: 查询流量包详情
✅ 查询成功，返回 2 个流量包

   流量包 1:
   - ID: fr-xxxxxxxxxxxxxxxx
   - 总流量: 1000.0 GB
   - 已用流量: 350.5 GB
   - 剩余流量: 649.5 GB
   - 使用率: 35.05%
   - 有效期: 2024-01-01T00:00:00Z ~ 2024-12-31T23:59:59Z
...

🎉 真实 API 调用测试全部通过！
```

## 获取流量包 ID

### 方法 1: 华为云控制台

1. 登录华为云控制台
2. 进入 **费用中心 > 资源包管理**
3. 找到 Flexus L 流量包
4. 复制资源 ID（格式：`fr-xxxxxxxxxxxxxxxx`）

### 方法 2: API 查询（待实现）

后续可通过 API 自动获取账户下的所有流量包列表。

## 常见问题

### Q1: 测试失败 - 认证错误

**错误信息：** `HTTP 403: Authentication failed`

**解决方案：**
- 检查 AK/SK 是否正确
- 确认 AK/SK 对应的账户有权限访问计费 API
- 验证 AK/SK 没有过期

### Q2: 测试失败 - 找不到资源

**错误信息：** `No resources found` 或返回空列表

**解决方案：**
- 检查流量包 ID 是否正确
- 确认流量包未过期（华为云限制：不能查询过期超过 18 个月的流量包）
- 验证流量包属于当前 AK/SK 对应的账户

### Q3: 如何切换到 BSS 域名？

**重要提示：** 当前实现使用的是 ECS 域名进行测试。真实调用时需要切换到 BSS 服务域名。

**计费 API 正确域名：**
- 中国站：`https://bss.myhuaweicloud.com`
- 国际站：`https://bss-intl.myhuaweicloud.com`

**修改方法：**
1. 更新 `HuaweiCloudClient.ENDPOINTS` 配置
2. 或创建专门的 `HuaweiCloudBSSClient` 类
3. 重新测试确保连通性

## 下一步

- [ ] 实现 BSS 客户端切换
- [ ] 添加流量包列表自动查询功能
- [ ] 集成到后端 API：`/api/v1/traffic/query`
- [ ] 添加前端流量监控页面

## 相关文档

- [华为云流量包查询 API 文档](https://support.huaweicloud.com/intl/zh-cn/api-flexusl/query_traffic_0001.html)
- [华为云 API 签名指南](https://support.huaweicloud.com/devg-apisign/api-sign-provide.html)
- 项目规则文档：`.warp/project-rules.md`
