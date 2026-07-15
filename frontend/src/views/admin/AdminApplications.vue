<template>
  <div class="page">
    <div class="page-header">
      <h1>All applications</h1>
      <p class="text-muted mb-0">Every student application across every drive.</p>
    </div>

    <div class="mb-3" style="max-width: 420px;">
      <input class="form-control" type="search" v-model="search" @input="onSearch"
        placeholder="Search by student, drive or company name…">
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!applications.length"
      :message="search ? `No applications match '${search}'.` : 'No applications yet.'"></empty-state>
    <div v-else class="card">
      <div class="table-responsive">
        <table class="table mb-0 align-middle">
          <thead><tr>
            <th>Student</th><th>Drive</th><th>Company</th><th>Applied</th><th>Status</th>
          </tr></thead>
          <tbody>
            <tr v-for="a in applications" :key="a.id">
              <td>{{ a.student_name }}</td>
              <td>{{ a.drive_title }}</td>
              <td class="text-muted">{{ a.company_name }}</td>
              <td>{{ a.applied_at ? a.applied_at.slice(0,10) : '' }}</td>
              <td><status-pill :status="a.status"></status-pill></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { api } from "@/services/api";

export default {
  name: "AdminApplications",
  data() {
    return { applications: [], loading: true, search: "", _debounce: null };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      const qs = this.search.trim() ? `?q=${encodeURIComponent(this.search.trim())}` : "";
      this.applications = await api.get(`/admin/applications${qs}`);
      this.loading = false;
    },
    onSearch() {
      clearTimeout(this._debounce);
      this._debounce = setTimeout(this.load, 300);
    },
  },
};
</script>
