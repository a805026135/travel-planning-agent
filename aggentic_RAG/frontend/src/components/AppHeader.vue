<script setup>
import { useAuth } from "../composables/useAuth.js";
import { useRouter, useRoute } from "vue-router";

const { username, isLoggedIn, logout } = useAuth();
const router = useRouter();
const route = useRoute();

function doLogout() { logout(); router.push("/"); }

const links = [
  { to: "/", label: "旅行规划", icon: "✈️" },
  { to: "/sessions", label: "我的规划", icon: "📋" },
  { to: "/knowledge", label: "知识库", icon: "📚" },
  { to: "/config", label: "系统配置", icon: "⚙️" },
];
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <!-- Logo -->
      <router-link to="/" class="logo">
        <span class="logo-icon">✈️</span>
        <span class="logo-text">旅行规划</span>
      </router-link>

      <!-- 导航链接 -->
      <nav class="topbar-nav">
        <router-link
          v-for="l in links" :key="l.to" :to="l.to"
          class="nav-item"
          :class="{ active: route.path === l.to }"
        >
          <span class="nav-icon">{{ l.icon }}</span>
          {{ l.label }}
        </router-link>
      </nav>

      <div class="topbar-spacer" />

      <!-- 用户区 -->
      <div class="topbar-user">
        <template v-if="!isLoggedIn">
          <router-link to="/login" class="nav-item">登录</router-link>
          <router-link to="/register" class="nav-item nav-cta">注册</router-link>
        </template>
        <template v-else>
          <div class="user-menu">
            <span class="user-avatar">{{ username[0]?.toUpperCase() || 'U' }}</span>
            <span class="user-name">{{ username }}</span>
            <button class="logout-btn" @click="doLogout">退出</button>
          </div>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  position: sticky; top: 0; z-index: 100;
  background: rgba(255,255,255,.92); backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--c-border); height: 60px;
}
.topbar-inner {
  max-width: var(--page-width); margin: 0 auto;
  display: flex; align-items: center; height: 100%;
  padding: 0 var(--s-6); gap: var(--s-1);
}
.logo {
  display: flex; align-items: center; gap: var(--s-2);
  text-decoration: none; font-weight: 700; font-size: 1.05rem;
  color: var(--c-text); margin-right: var(--s-4);
}
.logo-icon { font-size: 1.4rem; }
.logo-text { letter-spacing: -.02em; }
.topbar-nav { display: flex; align-items: center; gap: 2px; }
.nav-item {
  display: flex; align-items: center; gap: 4px; padding: 6px 12px;
  border-radius: 8px; font-size: .875rem; color: var(--c-text-secondary);
  text-decoration: none; transition: all var(--t-fast); font-weight: 500;
}
.nav-icon { font-size: 1rem; }
.nav-item:hover { background: var(--c-bg); color: var(--c-text); }
.nav-item.active { background: var(--c-primary-bg); color: var(--c-primary); }
.nav-cta {
  background: var(--c-primary); color: #fff !important;
  padding: 6px 16px; border-radius: 8px; margin-left: 4px;
}
.nav-cta:hover { background: var(--c-primary-dark) !important; color: #fff !important; }
.topbar-spacer { flex: 1; }
.topbar-user { display: flex; align-items: center; }
.user-menu { display: flex; align-items: center; gap: var(--s-3); }
.user-avatar {
  width: 32px; height: 32px; border-radius: 50%; background: var(--c-primary);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .875rem;
}
.user-name { font-size: .875rem; font-weight: 500; color: var(--c-text); }
.logout-btn {
  background: none; border: 1px solid var(--c-border); border-radius: 6px;
  padding: 4px 10px; font-size: .8rem; cursor: pointer; color: var(--c-text-secondary);
  font-family: var(--font); transition: all var(--t-fast);
}
.logout-btn:hover { border-color: var(--c-error); color: var(--c-error); }

@media (max-width: 640px) {
  .topbar-nav .nav-item { padding: 6px 8px; font-size: .8rem; }
  .nav-icon { display: none; }
  .logo-text { display: none; }
}
</style>
