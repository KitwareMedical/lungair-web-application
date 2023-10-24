import { defineStore } from 'pinia';
import { Ref, ref } from 'vue';
import { useLocalStorage } from '@vueuse/core';

export const useLocalFHIRStore = defineStore('local-fhir-store', () => {
  const { VITE_LOCAL_FHIR_SERVER_NAME, VITE_LOCAL_FHIR_SERVER_URL, VITE_PATIENT_IDENTIFIER  } = import.meta.env;

  // GUI display name
  const hostName = VITE_LOCAL_FHIR_SERVER_NAME
    ? ref(VITE_LOCAL_FHIR_SERVER_NAME)
    : useLocalStorage<string>('localFHIRServerHostName', '');

  // URL
  const hostURL = VITE_LOCAL_FHIR_SERVER_URL
    ? ref(VITE_LOCAL_FHIR_SERVER_URL)
    : useLocalStorage<string | null>('localFHIRServerHostURL', ''); // null if cleared by vuetify text input

  const identifierSystem = ref(VITE_PATIENT_IDENTIFIER);

  const currentPatientId = ref<string>('');

  function setCurrentPatient(id: string) {
    currentPatientId.value = id;
    console.log('currentPatient is: ', currentPatientId.value);
  }

  function getCurrentPatient(): Ref<string> {
    return currentPatientId;
  }

  return {
    hostURL,
    hostName,
    identifierSystem,
    setCurrentPatient,
    getCurrentPatient,
  };
});
