<template>
  <div v-if="error" class="invalid-feedback d-block">{{ error }}</div>
</template>

<script>
export default {
  name: "FieldError",
  props: ["error"],
};
</script>
