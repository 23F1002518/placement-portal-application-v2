<template>
  <nav class="navbar navbar-expand-md app-navbar">
    <div class="container">
      <router-link class="navbar-brand" to="/">Placement Portal</router-link>

      <div class="d-flex align-items-center gap-3 ms-auto">
        <template v-if="role === 'admin'">
          <router-link class="nav-link" to="/admin">Dashboard</router-link>
          <router-link class="nav-link" to="/admin/companies">Companies</router-link>
          <router-link class="nav-link" to="/admin/students">Students</router-link>
          <router-link class="nav-link" to="/admin/drives">Drives</router-link>
          <router-link class="nav-link" to="/admin/applications">Applications</router-link>
          <router-link class="nav-link" to="/admin/reports">Reports</router-link>
        </template>
        <template v-else-if="role === 'company'">
          <router-link class="nav-link" to="/company">Dashboard</router-link>
        </template>
        <template v-else-if="role === 'student'">
          <router-link class="nav-link" to="/student">Drives</router-link>
          <router-link class="nav-link" to="/student/applications">My Applications</router-link>
          <router-link class="nav-link" to="/student/profile">Profile</router-link>
        </template>

        <span v-if="user" class="text-muted small d-none d-md-inline">{{ displayName }}</span>
        <button v-if="user" class="btn btn-sm btn-outline-secondary" @click="logout">Log out</button>
      </div>
    </div>
  </nav>
</template>

<script>
import { useAuthStore } from "@/stores/auth";

export default {
  name: "Navbar",
  setup() {
    return { store: useAuthStore() };
  },
  computed: {
    role() {
      return this.store.role;
    },
    user() {
      return this.store.user;
    },
    displayName() {
      if (!this.store.user) return "";
      if (this.store.user.profile && this.store.user.profile.name) return this.store.user.profile.name;
      return this.store.user.email;
    },
  },
  methods: {
    logout() {
      this.store.clearAuth();
      this.$router.push("/login");
    },
  },
};
</script>
