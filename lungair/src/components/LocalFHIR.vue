<script setup lang="ts">
import { ref } from 'vue';
import FHIR from 'fhirclient';
import $ from 'jquery';
import { storeToRefs } from 'pinia';
import { useLocalFHIRStore } from '../store/local-fhir-store';

const patients = ref<{id: string, name: string}[]>([]);
const localFHIRStore = useLocalFHIRStore();
const { hostURL: localServerUrl, identifierSystem } = storeToRefs(localFHIRStore);
const errorAlert = ref("");
const doLoginLoading = ref(false);
const activePatientId = ref("");
type PatientIdentifier = { system: string, value: string };

async function login() {
  try {
    const client = await FHIR.client({
        serverUrl: localServerUrl.value
    });

    // Resolves with a Bundle or rejects with an Error
    const response = await client.request(`Patient?identifier=${identifierSystem.value}%7C`);

    for(let i = 0; i < response.entry?.length; ++i) {
      const patientResource = response.entry[i]?.resource;
      if (patientResource) {
        const nameObj = patientResource.name[0];
        const nameText = `${nameObj.given[0]} ${nameObj.family}`;

        const idValue: string | undefined =
          (patientResource.identifier as PatientIdentifier[]).find(elem => elem.system === identifierSystem.value)?.value;

        if (idValue) {
          patients.value?.push({id: idValue, name: nameText});
        } else {
          throw Error("No valid ID found, skipping patient entry.");
        }
      }
    }
    errorAlert.value = "";
    if (!response.entry) {
      errorAlert.value = "No records found.";
    } else {
      $('#localfhir-login-button').hide();
    }
  } catch (error) {
    errorAlert.value = "Failed to connect to the local FHIR server.";
  }
  doLoginLoading.value = false;
}

const doLogin = () => {
  doLoginLoading.value = true;
  login();
};

const setPatient = (id: string) => {
  localFHIRStore.setCurrentPatient(id);
  activePatientId.value = id;
}

</script>

<template>
  <div class="overflow-y-auto overflow-x-auto ma-2 fill-height">
    <v-list-subheader>Local FHIR Server</v-list-subheader>
    <v-container>
      <v-row class="mb-3" id="localfhir-login-button">
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
    </v-container>
    <v-alert
      v-if="errorAlert.length > 0"
      color="red"
      type="warning"
      transition="slide-y-transition"
    >
      {{ errorAlert }}
    </v-alert>
    <v-card class="mx-auto overflow-y-auto" max-height="500px">
      <v-list>
        <v-list-item
          v-for="patient in patients"
          :key="patient.id"
          :active="localFHIRStore.getCurrentPatient().value == patient.id"
          active-color="green"
          @click="setPatient(patient.id);"
          >
          {{ `${patient.name} (ID: ${patient.id})` }}
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<style scoped>

.volume-card {
  padding: 8px;
  cursor: pointer;
}

</style>
