<template>
  <div>
    <component-navbar v-if="store.token"></component-navbar>
    <router-view></router-view>
  </div>
</template>

<script>
import { useAuthStore } from "@/stores/auth";

export default {
  name: "App",
  setup() {
    return { store: useAuthStore() };
  },
};
</script>
