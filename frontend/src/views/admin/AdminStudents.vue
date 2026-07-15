<template>
  <div class="page">
    <div class="page-header d-flex justify-content-between align-items-end flex-wrap gap-2">
      <div>
        <h1>Students</h1>
        <p class="text-muted mb-0">Search students and manage their standing.</p>
      </div>
      <input class="form-control" style="max-width: 280px" placeholder="Search students…"
        v-model="q" @keyup.enter="load">
    </div>

    <loading-spinner v-if="loading"></loading-spinner>
    <empty-state v-else-if="!students.length" message="No students found."></empty-state>
    <div v-else class="card">
      <div class="table-responsive">
        <table class="table mb-0 align-middle">
          <thead><tr>
            <th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Year</th><th>Standing</th><th></th>
          </tr></thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td>{{ s.name }}</td>
              <td class="text-muted">{{ s.email }}</td>
              <td>{{ s.branch }}</td>
              <td>{{ s.cgpa }}</td>
              <td>{{ s.graduation_year }}</td>
              <td>
                <status-pill v-if="s.blacklisted" status="Blacklisted"></status-pill>
                <status-pill v-else-if="!s.active" status="Rejected"></status-pill>
                <status-pill v-else status="Active"></status-pill>
              </td>
              <td class="text-end">
                <div class="btn-group btn-group-sm">
                  <button v-if="s.active && !s.blacklisted" class="btn btn-outline-danger" @click="blacklist(s)">Blacklist</button>
                  <button v-if="!s.active || s.blacklisted" class="btn btn-outline-primary" @click="reinstate(s)">Reinstate</button>
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
  name: "AdminStudents",
  data() {
    return { students: [], q: "", loading: true };
  },
  async mounted() {
    await this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      this.students = await api.get(`/admin/students?q=${encodeURIComponent(this.q)}`);
      this.loading = false;
    },
    async blacklist(s) {
      await api.post(`/admin/user/${s.id}/blacklist`);
      await this.load();
    },
    async reinstate(s) {
      await api.post(`/admin/user/${s.id}/activate`);
      await this.load();
    },
  },
};
</script>
