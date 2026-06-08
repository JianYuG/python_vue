<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="home-header">
      <h2 class="logo">地图管理系统</h2>
      <div class="user-area">
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-avatar :size="28" icon="UserFilled" />
            <span class="username">{{ userStore.userInfo?.nickname || userStore.userInfo?.username || '用户' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout" divided>
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 地图主区域 -->
    <main class="home-main">
      <MapView />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import MapView from './MapView.vue'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  // 页面加载时刷新用户信息
  if (userStore.isLoggedIn() && !userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }
})

async function handleCommand(command) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch (error) {
      // 用户取消
    }
  }
}
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 24px;
  height: 48px;
  flex-shrink: 0;
  z-index: 100;
}

.logo {
  margin: 0;
  font-size: 18px;
  color: #409eff;
}

.user-area {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
}

.username {
  font-size: 13px;
}

.home-main {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
