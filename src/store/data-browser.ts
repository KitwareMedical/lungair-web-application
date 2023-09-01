import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useDataBrowserStore = defineStore('data-browser', () => {
  const hideSampleData = ref(true);
  return {
    hideSampleData,
  };
});
