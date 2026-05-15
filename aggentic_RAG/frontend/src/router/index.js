import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import SessionsView from "../views/SessionsView.vue";
import KnowledgeBaseView from "../views/KnowledgeBaseView.vue";
import ConfigView from "../views/ConfigView.vue";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView, meta: { title: "旅行规划" } },
  { path: "/sessions", name: "sessions", component: SessionsView, meta: { title: "我的规划" } },
  { path: "/knowledge", name: "knowledge", component: KnowledgeBaseView, meta: { title: "知识库" } },
  { path: "/config", name: "config", component: ConfigView, meta: { title: "系统配置" } },
  { path: "/login", name: "login", component: LoginView, meta: { title: "登录", guest: true } },
  { path: "/register", name: "register", component: RegisterView, meta: { title: "注册", guest: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
