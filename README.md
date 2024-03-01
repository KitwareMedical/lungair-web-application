# LungAIR web application by Kitware, Inc.

A customized version of VolView for bringing AI-based BPD risk prediction into the NICU.
Created by forking from [VolView](https://github.com/kitware/volview).

_This project is in active development and may change from version to version without notice._

## Usage

Following are instructions to build and run an instance of the LungAIR web application with
locally hosted DICOMWeb server, electronic health records (EHR) server, and VolView's
backend Python server for a connected deep learning pipeline.

### Prerequisites
- _Node-js_ version `18.17.1`
- _Python_ >= `3.9.12` (might work with lower versions, but not tested)
- Download and install [Orthanc Server](https://www.orthanc-server.com/download.php)
  with DICOMWeb plugin for locally hosting DICOM images.
  _Orthanc_ server should automatically start at http://localhost:8042/ once you restart the
  computer. On Linux you can instead use Docker following [this guide](/lungair/orthanc-docker-quickstart.md).
  For instructions on how to install Docker Engine in Linux, please follow the guide [here](https://docs.docker.com/engine/install/ubuntu/).

### Build and run the web app

Clone the repository to your local drive:

```bash
git clone https://www.github.com/KitwareMedical/lungair-web-application
cd lungair-web-application
git submodule update --init
```

Build and run VolView on http://localhost:4173/

```bash
npm install
npm run build
npm run preview
```

Start the proxy server to bypass CORS restrictions on _Orthanc_ server (for testing only):

```bash
cd lungair-web-application/lungair/orthanc-proxy
npm install
npm run dev
```
This should start a _vite_ http server at port 5173 as a proxy to the _Orthanc_ DICOMWeb
server already running on your machine.

### Run the python backend server

Follow instructions provided in the [lungair/server/README](./lungair/server/README.md) for details on installing and running the server.

### Electronic health records (EHR)

The LungAIR web application can interact with EHR in a few different ways.

#### Cerner/Oracle test patient login

This proof-of-concept demonstrates user authentication and data retrieval from a Cerner FHIR server.

Go to the _Patients_ tab in the LungAIR web application. The login process is currently hard-coded for
performing a Cerner Code app launch. Click the login and enter credentials in the
pop-up window. See this [test data document](https://docs.google.com/document/d/10RnVyF1etl_17pyCyK96tyhUWRbrTyEcqpwzW-Z-Ybs/edit)
for credentials to use on the public test server.

#### Local FHIR server using data from the LungAIR research group

Our research group has collected data from the NICU at Children's National Medical Center.
Using [fhir-sandbox](https://github.com/KitwareMedical/fhir-sandbox), we can create a local FHIR server
that is pre-populated with this data, and the LungAIR Web application will eventually be able to interact with this data.
If you do not have access to this data table, then you can still explore the features of the application
with synthetic data.

To set up the local FHIR server:

1. Go through the [initial fhir-sandbox setup](https://github.com/KitwareMedical/fhir-sandbox#initial-setup).
   When setting up a python environment within which to later run the fhir-sandbox scripts, you should additionally
   `pip install` the following packages: `openpyxl`, `scipy`.
   We assume that the FHIR server is now running and listening at port 3000.
2. Edit `lungair/fhir-sandbox-config/lungair_data_source.json` and set `data_file_path` to point to the LungAIR NICU data table.
   If you do not have this table, then simply set `data_file_path` to be `null` to enable synthetic data generation.
   The purpose of the synthetic data is only to demo the software interface. With the synthetic data option, you may also
   customize the patient IDs by setting `id_list` to the be the desired list of ID values.
3. Populate the FHIR server with the data from the table:
   ```bash
   # (replace the placeholders in these commands)
   cd [fhir-sandbox repository directory]
   python populate_fhir_server.py --json_file [lungair-web-application directory]/lungair/fhir-sandbox-config/lungair_data_source.json --fhir_server http://localhost:3000/hapi-fhir-jpaserver/fhir/
   ```
4. If you used custom data from a file/table, you must modify the [.env file](https://github.com/KitwareMedical/lungair-web-application/blob/main/.env) and set the
   environment variable
   ```
   VITE_PATIENT_IDENTIFIER="ID column from original data excel spreadsheet"
   ```
   The variable `VITE_PATIENT_IDENTIFIER` defines EHR's HL7 standard's [Identifier System](https://hl7.org/fhir/R4/datatypes-definitions.html#Identifier.system)
   which essentially is a string or URL describing the namespace of the identifier value (e.g. New York State Driver's License Number).

### Add images to the DICOMWeb server

LungAIR is meant to use images only alongside patient medical records, so any custom DICOM data that is uploaded needs to contain patient IDs that match the IDs in the EHR system.

To upload images, open http://localhost:8042/ in a browser window and click _All Studies_ button at the bottom,
then click the _Upload_ button in the top-right corner.

Now open LungAIR in another browser window using http://localhost:4173/.
Select a patient from the _Patients_ tab in LungAIR.
The _Images_ tab will then list the DICOM data that was uploaded to _Orthanc_ server, but only those images that have a patient ID in their DICOM header that matches the EHR ID of the selected patient. The variable `VITE_PATIENT_IDENTIFIER` described above is the identifier system that is used to match EHR IDs with DICOM patient IDs.

## Acknowledgments

This work was supported by the National Institutes of Health under Award Number R42HL145669.
The content is solely the responsibility of the authors and does not necessarily represent
the official views of the National Institutes of Health.

---

<img src="lungair/resources/logo.png" width=300 />
