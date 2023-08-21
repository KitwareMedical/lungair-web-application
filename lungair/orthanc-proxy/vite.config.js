import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      "/dicom-web": {
        target: "http://localhost:8042",
        changeOrigin: true,
        // auth: "orthanc:orthanc",
        configure: (proxy) => {
        // proxy will be an instance of 'http-proxy'
          proxy.on("proxyRes", function (proxyRes, req, res) {
            res.setHeader("Access-Control-Allow-Origin", "*");
            res.setHeader("Access-Control-Allow-Methods", "POST, GET, OPTIONS");
          });
        },
      },
    },
  },
});
