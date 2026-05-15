<script setup>
import { useRoute } from "vue-router";
import AppHeader from "./components/AppHeader.vue";
import ToastContainer from "./components/ToastContainer.vue";

const route = useRoute();
</script>

<template>
  <AppHeader />
  <router-view />
  <ToastContainer />

  <!-- 移动端底部导航 -->
  <nav class="mobile-nav">
    <router-link to="/" :class="{ active: route.path === '/' }"><span class="nav-icon">✈️</span><span>规划</span></router-link>
    <router-link to="/sessions" :class="{ active: route.path === '/sessions' }"><span class="nav-icon">📋</span><span>记录</span></router-link>
    <router-link to="/knowledge" :class="{ active: route.path === '/knowledge' }"><span class="nav-icon">📚</span><span>知识库</span></router-link>
    <router-link to="/config" :class="{ active: route.path === '/config' }"><span class="nav-icon">⚙️</span><span>配置</span></router-link>
  </nav>
</template>
