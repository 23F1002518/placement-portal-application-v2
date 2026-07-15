<template>
  <div class="page">
    <div class="page-header d-flex justify-content-between align-items-end flex-wrap gap-2">
      <div>
        <h1>Placement drives</h1>
        <p class="text-muted mb-0">Review and approve drives created by companies.</p>
      </div>
      <select class="form-select" style="max-width: 200px" v-model="statusFilter" @change="load">
        <option value="">All statuses</option>
        <option value="Pending">Pending</option>
        <option value="Approved">Approved</option>
        <option value="Rejected">Rejected</option>
        <option value="Closed">Closed</option>
      </select>
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!drives.length" message="No drives found."></empty-state>
    <div v-else class="card">
      <div class="table-responsive">
        <table class="table mb-0 align-middle">
          <thead><tr>
            <th>Title</th><th>Company</th><th>Min CGPA</th><th>Deadline</th><th>Status</th><th></th>
          </tr></thead>
          <tbody>
            <tr v-for="d in drives" :key="d.id">
              <td>{{ d.title }}</td>
              <td class="text-muted">{{ d.company_name }}</td>
              <td>{{ d.min_cgpa }}</td>
              <td>{{ d.deadline }}</td>
              <td><status-pill :status="d.status"></status-pill></td>
              <td class="text-end">
                <div class="btn-group btn-group-sm" v-if="d.status === 'Pending'">
                  <button class="btn btn-outline-primary" @click="approve(d)">Approve</button>
                  <button class="btn btn-outline-danger" @click="reject(d)">Reject</button>
                </div>
              </td>
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
  name: "AdminDrives",
  data() {
    return { drives: [], statusFilter: "", loading: true };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      const qs = this.statusFilter ? `?status=${this.statusFilter}` : "";
      this.drives = await api.get(`/admin/drives${qs}`);
      this.loading = false;
    },
    async approve(d) {
      await api.post(`/admin/drive/${d.id}/approve`);
      await this.load();
    },
    async reject(d) {
      await api.post(`/admin/drive/${d.id}/reject`);
      await this.load();
    },
  },
};
</script>
