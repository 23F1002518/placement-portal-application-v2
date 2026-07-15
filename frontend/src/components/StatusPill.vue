<template>
  <span class="pill" :class="'pill-' + status.toLowerCase()">{{ status }}</span>
</template>

<script>
export default {
  name: "StatusPill",
  props: ["status"],
};
</script>
