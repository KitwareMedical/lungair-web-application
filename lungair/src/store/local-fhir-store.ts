import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useLocalStorage } from '@vueuse/core';

export const useLocalFHIRStore = defineStore('local-fhir-store', () => {
  const { VITE_LOCAL_FHIR_SERVER_NAME, VITE_LOCAL_FHIR_SERVER_URL } = import.meta.env;

  // GUI display name
  const hostName = VITE_LOCAL_FHIR_SERVER_NAME
    ? ref(VITE_LOCAL_FHIR_SERVER_NAME)
    : useLocalStorage<string>('localFHIRServerHostName', '');

  // URL
  const hostURL = VITE_LOCAL_FHIR_SERVER_URL
    ? ref(VITE_LOCAL_FHIR_SERVER_URL)
    : useLocalStorage<string | null>('localFHIRServerHostURL', ''); // null if cleared by vuetify text input

  return {
    hostURL,
    hostName,
  };
});
