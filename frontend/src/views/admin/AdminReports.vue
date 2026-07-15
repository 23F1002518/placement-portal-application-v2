<template>
  <div class="page">
    <div class="page-header">
      <h1>Reports</h1>
      <p class="text-muted mb-0">Placement activity at a glance.</p>
    </div>
    <loading-spinner v-if="loading"></loading-spinner>
    <div v-else class="row g-3">
      <div class="col-md-6">
        <div class="card"><div class="card-body">
          <h2 class="h6 mb-3">Applications by status</h2>
          <canvas ref="statusChart" height="220"></canvas>
        </div></div>
      </div>
      <div class="col-md-6">
        <div class="card"><div class="card-body">
          <h2 class="h6 mb-3">Drives created per month</h2>
          <canvas ref="monthChart" height="220"></canvas>
        </div></div>
      </div>
      <div class="col-12">
        <div class="card"><div class="card-body">
          <h2 class="h6 mb-3">Placements per company</h2>
          <table class="table mb-0">
            <thead><tr><th>Company</th><th>Students selected</th></tr></thead>
            <tbody>
              <tr v-for="r in data.placements_per_company" :key="r.company">
                <td>{{ r.company }}</td><td>{{ r.count }}</td>
              </tr>
            </tbody>
          </table>
        </div></div>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart } from "chart.js";
import { api } from "@/services/api";

export default {
  name: "AdminReports",
  data() {
    return { data: null, loading: true };
  },
  async mounted() {
    this.data = await api.get("/admin/reports");
    this.loading = false;
    this.$nextTick(() => this.renderCharts());
  },
  methods: {
    renderCharts() {
      const statusCtx = this.$refs.statusChart.getContext("2d");
      new Chart(statusCtx, {
        type: "doughnut",
        data: {
          labels: this.data.applications_by_status.map((r) => r.status),
          datasets: [
            {
              data: this.data.applications_by_status.map((r) => r.count),
              backgroundColor: ["#2563eb", "#93c5fd", "#16a34a", "#f59e0b"],
            },
          ],
        },
        options: { plugins: { legend: { position: "bottom" } } },
      });

      const monthCtx = this.$refs.monthChart.getContext("2d");
      new Chart(monthCtx, {
        type: "bar",
        data: {
          labels: this.data.drives_per_month.map((r) => `${r.month}/${r.year}`),
          datasets: [{ label: "Drives created", data: this.data.drives_per_month.map((r) => r.count), backgroundColor: "#2563eb" }],
        },
        options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
      });
    },
  },
};
</script>
