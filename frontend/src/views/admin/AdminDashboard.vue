<template>
  <div class="page">
    <div class="page-header">
      <h1>Admin dashboard</h1>
      <p class="text-muted mb-0">Institute-wide placement overview.</p>
    </div>
    <loading-spinner v-if="loading"></loading-spinner>
    <div v-else class="row g-3">
      <div class="col-6 col-md-3">
        <div class="stat-tile">
          <div class="stat-value">{{ stats.students }}</div>
          <div class="stat-label">Students</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-tile">
          <div class="stat-value">{{ stats.companies }}</div>
          <div class="stat-label">Companies</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-tile">
          <div class="stat-value">{{ stats.drives }}</div>
          <div class="stat-label">Placement drives</div>
        </div>
      </div>
      <div class="col-6 col-md-3">
        <div class="stat-tile">
          <div class="stat-value">{{ stats.applications }}</div>
          <div class="stat-label">Applications</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "AdminDashboard",
  data() {
    return { stats: null, loading: true };
  },
  async mounted() {
    this.stats = await api.get("/admin/dashboard");
    this.loading = false;
  },
};
</script>
