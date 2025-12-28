<template>
  <div class="home">
    <el-container>
      <el-header>
        <h1>华为云服务器流量监控系统</h1>
      </el-header>
      <el-main>
        <el-card class="welcome-card">
          <template #header>
            <div class="card-header">
              <span>欢迎使用</span>
            </div>
          </template>
          <div class="content">
            <p>系统正在开发中...</p>
            <p>版本: v0.1.0-alpha</p>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
// 首页组件
</script>

<style scoped>
.home {
  height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-main {
  padding: 20px;
}

.welcome-card {
  max-width: 600px;
  margin: 50px auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.content {
  text-align: center;
  padding: 20px;
}

.content p {
  margin: 10px 0;
  font-size: 16px;
}
</style>
