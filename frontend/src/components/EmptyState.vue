<template>
  <div class="empty-state text-center py-5 text-muted">
    <p class="mb-0">{{ message }}</p>
  </div>
</template>

<script>
export default {
  name: "EmptyState",
  props: { message: { type: String, default: "Nothing here yet." } },
};
</script>
