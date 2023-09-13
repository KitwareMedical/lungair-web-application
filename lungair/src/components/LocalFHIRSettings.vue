<script lang="ts">
import { defineComponent } from 'vue';
import { useLocalFHIRStore } from '../store/local-fhir-store';

export default defineComponent({
  setup() {
    const localFHIRStore = useLocalFHIRStore();

    return {
      localFHIRStore,
    };
  },
});
</script>

<template>
  <div>
    <h3 class="mb-4">Local FHIR Server</h3>
    <v-text-field
      v-model="localFHIRStore.hostName"
      class="server-param"
      label="Host Display Name"
      clearable
    />
    <v-text-field
      v-model="localFHIRStore.hostURL"
      class="server-param"
      label="Host Address"
      clearable
    />
  </div>
</template>
