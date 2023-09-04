<script setup lang="ts">
import { ref } from 'vue';
import FHIR from 'fhirclient';

const patients = ref<string[]>([]);
// const localServerUrl = ref("https://r4.smarthealthit.org");
const localServerUrl = ref("http://localhost:3000/hapi-fhir-jpaserver/fhir");

async function cernerLogin() {
  console.log('connecting to local FHIR server.');

  const client = await FHIR.client({
      serverUrl: localServerUrl.value
  });

  // Resolves with a Bundle or rejects with an Error
  const res = await client.request("Patient");

  for(let i = 0; i < res.entry.length; ++i) {
    const nameObj = res.entry[i]?.resource?.name[0];
    const nameText = `${nameObj.given[0]} ${nameObj.family}`;
    patients.value.push(nameText);
  }
  console.log(patients.value);
}

const doCernerLoginLoading = ref(false);
const doCernerLogin = async () => {
  doCernerLoginLoading.value = true;
  try {
    cernerLogin();
  } finally {
    doCernerLoginLoading.value = false;
  }
};
</script>

<template>
  <div class="overflow-y-auto overflow-x-auto ma-2 fill-height">
    <v-list-subheader>Local FHIR Server</v-list-subheader>
    <v-container>
      <v-row id="login-button" class="ma-1">
        <v-text-field class="mr-3"
          label="URL:"
          :model-value="localServerUrl"
          @update:modelValue="newValue => localServerUrl = newValue"
          type="string"
          variant="outlined"
          density="compact"
          expanding
        />
        <v-btn
          variant="tonal"
          prepend-icon="mdi-lan-connect"
          @click="doCernerLogin"
          :loading="doCernerLoginLoading">
          Connect
        </v-btn>
      </v-row>
      <div class="overflow-y-auto overflow-x-hidden ma-1">
        <v-row
          v-for="(patientName, index) in patients"
          :key="index"
          class="ml-1"
        >
        {{ patientName }}
        </v-row>
      </div>
    </v-container>
  </div>
</template>
