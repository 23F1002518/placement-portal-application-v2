<template>
  <div class="page">
    <div class="page-header d-flex justify-content-between align-items-end flex-wrap gap-2">
      <div>
        <h1>Companies</h1>
        <p class="text-muted mb-0">Approve registrations and manage company standing.</p>
      </div>
      <input class="form-control" style="max-width: 280px" placeholder="Search companies…"
        v-model="q" @keyup.enter="load">
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!companies.length" message="No companies found."></empty-state>
    <div v-else class="card">
      <div class="table-responsive">
        <table class="table mb-0 align-middle">
          <thead><tr>
            <th>Name</th><th>Email</th><th>HR contact</th><th>Status</th><th>Standing</th><th></th>
          </tr></thead>
          <tbody>
            <tr v-for="c in companies" :key="c.id">
              <td>{{ c.name }}</td>
              <td class="text-muted">{{ c.email }}</td>
              <td>{{ c.hr_contact }}</td>
              <td><status-pill :status="c.approved ? 'Approved' : 'Pending'"></status-pill></td>
              <td>
                <status-pill v-if="c.blacklisted" status="Blacklisted"></status-pill>
                <status-pill v-else-if="!c.active" status="Rejected"></status-pill>
                <status-pill v-else status="Active"></status-pill>
              </td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <button v-if="!c.approved" class="btn btn-outline-primary" @click="approve(c)">Approve</button>
                  <button v-if="!c.approved" class="btn btn-outline-danger" @click="reject(c)">Reject</button>
                  <button v-if="c.active && !c.blacklisted" class="btn btn-outline-danger" @click="blacklist(c)">Blacklist</button>
                  <button v-if="!c.active || c.blacklisted" class="btn btn-outline-primary" @click="reinstate(c)">Reinstate</button>
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
  name: "AdminCompanies",
  data() {
    return { companies: [], q: "", loading: true };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      this.companies = await api.get(`/admin/companies?q=${encodeURIComponent(this.q)}`);
      this.loading = false;
    },
    async approve(c) {
      await api.post(`/admin/company/${c.id}/approve`);
      await this.load();
    },
    async reject(c) {
      await api.post(`/admin/company/${c.id}/reject`);
      await this.load();
    },
    async blacklist(c) {
      await api.post(`/admin/user/${c.id}/blacklist`);
      await this.load();
    },
    async reinstate(c) {
      await api.post(`/admin/user/${c.id}/activate`);
      await this.load();
    },
  },
};
</script>
