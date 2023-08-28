<script setup lang="ts">
import { ref } from 'vue';
import FHIR from 'fhirclient';
import $ from 'jquery';

// --- CERNER EHR --- //

function processOAuthMessage(msg: any) {
  sessionStorage[msg.storage.key] = msg.storage.value;
  window.history.pushState("object or string", "Title", `/?code=${msg.code}&state=${msg.state}`);
  FHIR.oauth2.ready()
      .then((fhirClient) => {
        return fhirClient.request("Patient");
      })
      .then((info) => {
        const element = document.getElementById('PatientInfoArea');
        const patientInfo = info?.entry[0]?.resource;
        if (element && patientInfo) {
          $('#ptable').show();
          $('#login-button').hide();
          $('#pid').html(patientInfo.id);
          $('#pname').html(patientInfo.name[0].text);
          $('#pdob').html(patientInfo.birthDate);
          $('#pgender').html(patientInfo.gender);
          $('#paddr').html(patientInfo.address[0].text);
        }
      }).catch(console.error);
}

function cernerLogin() {
  const screenWidth = 1920;
  const screenHeight = 1080;
  const width = 780;
  const height = 550;
  const left = (screenWidth - width) / 2;
  let top = (screenHeight - height) / 2;
  const uniqueWindowId = '_blank';
  if (top > 20) {
    top -= 20;
  }
  let params = `width=${width}, height=${height}`;
  params += `, top=${top}, left=${left}`;
  params += ', titlebar=no, location=no, popup=yes';
  const url = "http://localhost:4173/lungair/fhir-login/launch.html?iss=https://fhir-myrecord.cerner.com/dstu2/ec2458f2-1e24-41c8-b71b-0e701af7583d";
  const loginWindow = window.open(url, uniqueWindowId, params);
  window.addEventListener("message", (e) => {
    const oauthMessage = e.data;
    loginWindow?.close();
    if (oauthMessage && oauthMessage.url && oauthMessage.code && oauthMessage.state && oauthMessage.storage) {
      processOAuthMessage(oauthMessage);
    }
  }, false);
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
    <v-divider />
    <v-list-subheader>Cerner EHR</v-list-subheader>
    <div id="ptable" style="font-size:0.8rem" hidden>
      <v-row class="ma-2">
        <div id="PatientInfoArea">Current Patient</div>
        <v-divider />
      </v-row>
      <v-row>
        <v-col><b>ID</b></v-col>
        <v-col id="pid"></v-col>
      </v-row>
      <v-row>
        <v-col><b>Name</b></v-col>
        <v-col id="pname"></v-col>
      </v-row>
      <v-row>
        <v-col><b>DOB</b></v-col>
        <v-col id="pdob"></v-col>
      </v-row>
      <v-row>
        <v-col><b>Gender</b></v-col>
        <v-col id="pgender"></v-col>
      </v-row>
      <v-row>
        <v-col><b>Address</b></v-col>
        <v-col id="paddr"></v-col>
      </v-row>
    </div>
    <div>
      <v-row id="login-button" class="ma-1">
        <v-btn @click="doCernerLogin" :loading="doCernerLoginLoading">
          Login
        </v-btn>
      </v-row>
    </div>
    <v-divider />
  </div>
</template>
