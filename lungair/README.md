# LungAIR web application by Kitware, Inc.

A customized version of VolView for bringing AI-based BPD risk prediction into the NICU.
Created by forking from [VolView](https://github.com/kitware/volview).

_This project is in active development and may change from version to version without notice._

## Instructions to build and run the test server
Following are instructions to build and run an instance of LungAir web application with
locally hosted DICOMWeb server, electronics health records (EHR) server, and VolView's
backend Python server for a connected deep learning pipeline.

### Prerequisites
- _Node-js_ version >= `18.17.0` (might work with lower versions, but not tested)
- _Python_ >= `3.9.12` (might work with lower versions, but not tested)
- Download and install [Orthanc Server](https://www.orthanc-server.com/download.php)
  with DICOMWeb plugin for locally hosting DICOM images.
  _Orthanc_ server should automatically start at http://localhost:8042/ once you restart the
  computer.

### Build and Run
Once you have the pre-requisites, follow the steps listed below:

1. Clone the repository to your local drive:
    ```bash
    git clone https://www.github.com/KitwareMedical/lungair-web-application --branch=lungair-main
    cd lungair-web-application
    npm install
    ```

2. Build and run VolView on http://localhost:4173/ 

    Open a new console window, and run:
    ```bash
    npm run build
    npm run preview
    ```

3. Start proxy server to bypass CORS restrictions on _Orthanc_ server (for testing only).

    Open a new console window, and run:
    ```bash
    cd lungair-web-application/lungair/orthanc-proxy
    npm install
    npm run dev
    ```
    This should start a _vite_ http server at port 5173 as a proxy to the _Orthanc_ DICOMWeb
    server already running on your machine.

4. Prepare some input data.

    Open http://localhost:8042/ in a browser window and click _All Studies_ button at the bottom.
    If you do not already have any studies in your hosted DICOMWeb server, upload some example
    DICOM data by clicking the _Upload_ button in the top-right corner.

    Now open VolView in another browser window using http://localhost:4173/.
    The Data tab should list your DICOM data uploaded to _Orthanc_ server.

5. Electronic Health Records (EHR) data.

   Go to the _LungAir EHR_ tab in VolView. The login process is currently hard-coded for
   performing a Cerner Code app launch. Click the login and enter credentials in the
   pop-up window. See this [test data document](https://docs.google.com/document/d/10RnVyF1etl_17pyCyK96tyhUWRbrTyEcqpwzW-Z-Ybs/edit)
   for credentials to use on Oracle's public test server.

6. VolView Python backend server.

   VolView's python server can be used to run backend jobs such as deep learning inference pipelines.
   Start an instance of the python server by following the [quick-start guide](../documentation/content/doc/server-dev.md#starting-the-server).

## Acknowledgments

This work was supported by the National Institutes of Health under Award Number R42HL145669.
The content is solely the responsibility of the authors and does not necessarily represent
the official views of the National Institutes of Health.

---

<img src="../lungair/resources/logo.png" width=300 />
