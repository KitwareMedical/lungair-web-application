<script setup lang="ts">
import { computed, ref } from 'vue';
import { useCurrentImage } from '@/src/composables/useCurrentImage';
import { useServerStore, ConnectionState } from '@/src/store/server';
import { getDataID, makeImageSelection } from '@/src/store/datasets';
import { useImageStore } from '@/src/store/datasets-images';
import { useDatasetStore } from '@/src/store/datasets';
import { useSegmentGroupStore } from '@/src/store/segmentGroups';

const dataStore = useDatasetStore();
const imageStore = useImageStore();
const segmentGroupStore = useSegmentGroupStore();
const serverStore = useServerStore();
const { client } = serverStore;
const ready = computed(
  () => serverStore.connState === ConnectionState.Connected
);

// --- median filter --- //

const medianFilterLoading = ref(false);
const { currentImageID } = useCurrentImage();
const medianFilterRadius = ref(2);

const doMedianFilter = async () => {
  const id = currentImageID.value;
  if (!id) return;

  medianFilterLoading.value = true;
  try {
    await client.call('medianFilter', [id, medianFilterRadius.value]);
  } finally {
    medianFilterLoading.value = false;
  }
};

const hasCurrentImage = computed(() => !!currentImageID.value);

// --- lung segmentation --- //
const lungSegmentationLoading = ref(false);

const doLungSegmentation = async () => {
  const currId = currentImageID.value;
  if (!currId) return;

  lungSegmentationLoading.value = true;
  try {
    await client.call('segmentLungs', [currId]);

    const seg_id = Object.keys(imageStore.metadata).find(id => imageStore.metadata[id].name === `${currId}_seg`);
    const segIdString = seg_id?.toString();
    const primarySelection = dataStore.primarySelection;
    if (primarySelection && segIdString) {
      segmentGroupStore.convertImageToLabelmap(
        makeImageSelection(segIdString),
        primarySelection
      );
    }
  } finally {
    lungSegmentationLoading.value = false;
  }
};


</script>


<template>
  <div class="overflow-y-auto overflow-x-hidden ma-2 fill-height">
    <v-alert v-if="!ready" color="info">Not connected to the server.</v-alert>
    <v-divider />
    <v-list-subheader>Median Filter</v-list-subheader>
    <div>
      <v-row>
        <v-col cols="3">
          <v-text-field
            :model-value="medianFilterRadius"
            @update:model-value="medianFilterRadius = Number($event || 0)"
            type="number"
            variant="outlined"
            density="compact"
            hide-details
            placeholder="1"
          />
        </v-col>
        <v-col>
          <v-btn
            @click="doMedianFilter"
            :loading="medianFilterLoading"
            :disabled="!ready || !hasCurrentImage"
          >
            Run Median Filter
          </v-btn>
          <span v-if="!hasCurrentImage" class="ml-4 body-2">
            No image loaded
          </span>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <v-btn
            @click="doLungSegmentation"
            :loading="lungSegmentationLoading"
            :disabled="!ready || !hasCurrentImage"
          >
            Run Lung Segmentation
          </v-btn>
          <span v-if="!hasCurrentImage" class="ml-4 body-2">
            No image loaded
          </span>
        </v-col>
      </v-row>
    </div>
  </div>
</template>
