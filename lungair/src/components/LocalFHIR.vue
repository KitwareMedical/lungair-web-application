<script setup lang="ts">
import { ref } from 'vue';
import FHIR from 'fhirclient';
import { storeToRefs } from 'pinia';
import { useLocalFHIRStore } from '../store/local-fhir-store';

const patients = ref<string[]>([]);
const localFHIRStore = useLocalFHIRStore();
const { hostURL: localServerUrl } = storeToRefs(localFHIRStore);
const errorAlert = ref("");
const doLoginLoading = ref(false);

async function login() {
  try {
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
    errorAlert.value = "";
  } catch (error) {
    errorAlert.value = "Failed to connect to the local FHIR server.";
  }
  doLoginLoading.value = false;
}

const doLogin = () => {
  doLoginLoading.value = true;
  login();
};
</script>

<template>
  <div class="overflow-y-auto overflow-x-auto ma-2 fill-height">
    <v-list-subheader>Local FHIR Server</v-list-subheader>
    <v-container>
      <v-row class="mb-3" id="login-button">
        <v-btn
          class="primary"
          variant="tonal"
          prepend-icon="mdi-lan-connect"
          :loading="doLoginLoading"
          @click="doLogin"
        >
          Connect
        </v-btn>
      </v-row>
      <div class="overflow-y-auto overflow-x-hidden">
        <v-row
          v-for="(patientName, index) in patients"
          :key="index"
          class="ml-1"
        >
        {{ patientName }}
        </v-row>
      </div>
    </v-container>
    <v-alert
      v-if="errorAlert.length > 0"
      color="red"
      type="warning"
      transition="slide-y-transition"
    >
      {{ errorAlert }}
    </v-alert>
  </div>
</template>
